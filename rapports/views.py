from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import RapportSnapshot
from .serializers import RapportSnapshotSerializer
from transactions.models import Transaction
from categories.models import Categorie
from django.db.models import Sum
import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from authentication.permissions import IsAdminRole

MOIS_FR = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
           'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

# Thème clair pour PDF (professionnel, imprimable)
VERT        = colors.HexColor('#16A34A')
VERT_CLAIR  = colors.HexColor('#DCFCE7')
ROUGE       = colors.HexColor('#DC2626')
ROUGE_CLAIR = colors.HexColor('#FEE2E2')
BLEU_FONCE  = colors.HexColor('#1E293B')
GRIS_CLAIR  = colors.HexColor('#F8FAFC')
GRIS_MOYEN  = colors.HexColor('#E2E8F0')
TEXTE       = colors.HexColor('#0F172A')
TEXTE_DOUX  = colors.HexColor('#64748B')
BLANC       = colors.white


class RapportListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        rapports = RapportSnapshot.objects.filter(
            id_entreprise=request.user.id_entreprise
        )
        serializer = RapportSnapshotSerializer(rapports, many=True)
        return Response(serializer.data)


class RapportGenererView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        mois  = request.data.get('mois')
        annee = request.data.get('annee')

        if not mois or not annee:
            return Response(
                {'error': 'Mois et année sont obligatoires !'},
                status=status.HTTP_400_BAD_REQUEST
            )

        entreprise = request.user.id_entreprise

        total_entrees = Transaction.objects.filter(
            id_entreprise=entreprise,
            type='Entree',
            date_transaction__month=mois,
            date_transaction__year=annee
        ).aggregate(total=Sum('montant'))['total'] or 0

        total_sorties = Transaction.objects.filter(
            id_entreprise=entreprise,
            type='Sortie',
            date_transaction__month=mois,
            date_transaction__year=annee
        ).aggregate(total=Sum('montant'))['total'] or 0

        solde_final = total_entrees - total_sorties

        rapport, created = RapportSnapshot.objects.update_or_create(
            id_entreprise=entreprise,
            mois=mois,
            annee=annee,
            defaults={
                'total_entrees': total_entrees,
                'total_sorties': total_sorties,
                'solde_final':   solde_final,
            }
        )

        serializer = RapportSnapshotSerializer(rapport)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class RapportExportPDFView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        mois  = request.query_params.get('mois')
        annee = request.query_params.get('annee')

        if not mois or not annee:
            return Response({'error': 'Paramètres mois et annee requis.'}, status=400)

        mois  = int(mois)
        annee = int(annee)
        entreprise = request.user.id_entreprise
        nom_entreprise = entreprise.nom if hasattr(entreprise, 'nom') else str(entreprise)
        devise = getattr(entreprise, 'devise', 'XOF')

        # Transactions du mois
        transactions = Transaction.objects.filter(
            id_entreprise=entreprise,
            date_transaction__month=mois,
            date_transaction__year=annee,
        ).order_by('date_transaction')

        # Catégories pour résolution des noms
        cats = {c.id: c.nom_categorie for c in Categorie.objects.filter(id_entreprise=entreprise)}

        total_entrees = sum(float(t.montant) for t in transactions if t.type == 'Entree')
        total_sorties = sum(float(t.montant) for t in transactions if t.type == 'Sortie')
        solde_final   = total_entrees - total_sorties

        # --- Génération PDF ---
        response = HttpResponse(content_type='application/pdf')
        nom_fichier = f"rapport_{MOIS_FR[mois]}_{annee}_{nom_entreprise}.pdf".replace(' ', '_')
        response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'

        doc = SimpleDocTemplate(
            response,
            pagesize=A4,
            topMargin=2*cm,
            bottomMargin=2*cm,
            leftMargin=2*cm,
            rightMargin=2*cm,
        )

        elems = []

        def fmt(n):
            return f"{n:,.0f}".replace(',', ' ')

        # ── STYLES ──
        s_app    = ParagraphStyle('app',     fontSize=28, textColor=VERT,
                                  fontName='Helvetica-Bold', alignment=TA_CENTER,
                                  spaceBefore=0, spaceAfter=10, leading=34)
        s_sous   = ParagraphStyle('sous',    fontSize=12, textColor=TEXTE_DOUX,
                                  fontName='Helvetica', alignment=TA_CENTER,
                                  spaceBefore=0, spaceAfter=6, leading=16)
        s_period = ParagraphStyle('period',  fontSize=16, textColor=TEXTE,
                                  fontName='Helvetica-Bold', alignment=TA_CENTER,
                                  spaceBefore=0, spaceAfter=4, leading=20)
        s_ent    = ParagraphStyle('ent',     fontSize=13, textColor=TEXTE_DOUX,
                                  fontName='Helvetica', alignment=TA_CENTER,
                                  spaceBefore=0, spaceAfter=10, leading=17)
        s_titre  = ParagraphStyle('titre',   fontSize=13, textColor=TEXTE,
                                  fontName='Helvetica-Bold',
                                  spaceBefore=0, spaceAfter=0)
        s_pied   = ParagraphStyle('pied',    fontSize=8, textColor=TEXTE_DOUX,
                                  fontName='Helvetica', alignment=TA_CENTER)

        # ── EN-TÊTE ──
        elems.append(Paragraph('FinanceIQ', s_app))
        elems.append(Paragraph('Rapport Financier Mensuel', s_sous))
        elems.append(Paragraph(f'{MOIS_FR[mois]} {annee}', s_period))
        elems.append(Paragraph(nom_entreprise, s_ent))
        elems.append(HRFlowable(width='100%', thickness=2, color=VERT, spaceAfter=0))
        elems.append(Spacer(1, 0.4*cm))

        # ── KPIs ──
        solde_color = VERT if solde_final >= 0 else ROUGE
        solde_bg    = VERT_CLAIR if solde_final >= 0 else ROUGE_CLAIR

        kh = ParagraphStyle('kh', fontSize=8, textColor=TEXTE_DOUX, fontName='Helvetica-Bold', alignment=TA_CENTER, leading=11)
        kv_vert  = ParagraphStyle('kv_vert',  fontSize=14, textColor=VERT,        fontName='Helvetica-Bold', alignment=TA_CENTER, leading=18)
        kv_rouge = ParagraphStyle('kv_rouge', fontSize=14, textColor=ROUGE,       fontName='Helvetica-Bold', alignment=TA_CENTER, leading=18)
        kv_solde = ParagraphStyle('kv_solde', fontSize=14, textColor=solde_color, fontName='Helvetica-Bold', alignment=TA_CENTER, leading=18)

        kpi_data = [
            [
                Paragraph('<b>TOTAL ENTRÉES</b>', kh),
                Paragraph('<b>TOTAL SORTIES</b>', kh),
                Paragraph('<b>SOLDE DU MOIS</b>', kh),
            ],
            [
                Paragraph(f'<b>+ {fmt(total_entrees)} {devise}</b>', kv_vert),
                Paragraph(f'<b>- {fmt(total_sorties)} {devise}</b>', kv_rouge),
                Paragraph(f'<b>{"+ " if solde_final>=0 else ""}{fmt(solde_final)} {devise}</b>', kv_solde),
            ],
        ]
        kpi_table = Table(kpi_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (0,-1), VERT_CLAIR),
            ('BACKGROUND',    (1,0), (1,-1), ROUGE_CLAIR),
            ('BACKGROUND',    (2,0), (2,-1), solde_bg),
            ('BOX',           (0,0), (0,-1), 1, VERT),
            ('BOX',           (1,0), (1,-1), 1, ROUGE),
            ('BOX',           (2,0), (2,-1), 1, solde_color),
            ('TOPPADDING',    (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING',   (0,0), (-1,-1), 8),
            ('RIGHTPADDING',  (0,0), (-1,-1), 8),
            ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
            ('LINEAFTER',     (0,0), (1,-1),  0.5, GRIS_MOYEN),
        ]))
        elems.append(KeepTogether([kpi_table]))
        elems.append(Spacer(1, 0.6*cm))

        # ── TABLEAU TRANSACTIONS ──
        nb = len(transactions)
        elems.append(KeepTogether([
            Paragraph(f'Détail des transactions — {nb} opération{"s" if nb > 1 else ""}', s_titre),
            Spacer(1, 0.2*cm),
            HRFlowable(width='100%', thickness=0.5, color=GRIS_MOYEN, spaceAfter=0),
        ]))
        elems.append(Spacer(1, 0.2*cm))

        if not transactions:
            elems.append(Paragraph('Aucune transaction pour cette période.', s_sous))
        else:
            headers = ['Date', 'Libellé', 'Catégorie', 'Type', f'Montant ({devise})']
            rows    = [headers]

            for t in transactions:
                cat_nom     = cats.get(t.id_categorie_id, '—')
                is_entree   = t.type == 'Entree'
                montant_str = f"+ {fmt(float(t.montant))}" if is_entree else f"- {fmt(float(t.montant))}"
                rows.append([
                    t.date_transaction.strftime('%d/%m/%Y') if t.date_transaction else '—',
                    str(t.libelle or '—')[:38],
                    cat_nom[:22],
                    'Entrée' if is_entree else 'Sortie',
                    montant_str,
                ])

            col_w     = [2.5*cm, 6*cm, 3.5*cm, 2*cm, 3*cm]
            tx_table  = Table(rows, colWidths=col_w, repeatRows=1, splitByRow=1)

            row_styles = [
                # En-tête
                ('BACKGROUND',    (0,0), (-1,0),  BLEU_FONCE),
                ('TEXTCOLOR',     (0,0), (-1,0),  BLANC),
                ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
                ('FONTSIZE',      (0,0), (-1,0),  9),
                ('ALIGN',         (0,0), (-1,0),  'CENTER'),
                ('TOPPADDING',    (0,0), (-1,0),  8),
                ('BOTTOMPADDING', (0,0), (-1,0),  8),
                # Corps
                ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
                ('FONTSIZE',      (0,1), (-1,-1), 9),
                ('TEXTCOLOR',     (0,1), (-1,-1), TEXTE),
                ('ALIGN',         (4,1), (4,-1),  'RIGHT'),
                ('ALIGN',         (3,1), (3,-1),  'CENTER'),
                ('TOPPADDING',    (0,1), (-1,-1), 7),
                ('BOTTOMPADDING', (0,1), (-1,-1), 7),
                ('LEFTPADDING',   (0,0), (-1,-1), 7),
                ('RIGHTPADDING',  (0,0), (-1,-1), 7),
                # Bordures
                ('LINEBELOW',     (0,0), (-1,-1), 0.5, GRIS_MOYEN),
                ('LINEAFTER',     (0,0), (-2,-1), 0.3, GRIS_MOYEN),
                ('BOX',           (0,0), (-1,-1), 0.8, GRIS_MOYEN),
            ]

            # Alternance de couleurs + colorisation montants
            for i, t in enumerate(transactions, start=1):
                is_entree = t.type == 'Entree'
                bg = VERT_CLAIR if is_entree else ROUGE_CLAIR if not is_entree and i % 2 == 0 else GRIS_CLAIR
                if i % 2 == 0:
                    row_styles.append(('BACKGROUND', (0,i), (-1,i), GRIS_CLAIR))
                else:
                    row_styles.append(('BACKGROUND', (0,i), (-1,i), BLANC))
                row_styles.append(('TEXTCOLOR', (4,i), (4,i), VERT if is_entree else ROUGE))
                row_styles.append(('FONTNAME',  (4,i), (4,i), 'Helvetica-Bold'))

            tx_table.setStyle(TableStyle(row_styles))
            elems.append(tx_table)

        # ── PIED DE PAGE ──
        elems.append(Spacer(1, 0.6*cm))
        elems.append(HRFlowable(width='100%', thickness=0.5, color=GRIS_MOYEN, spaceAfter=0))
        elems.append(Spacer(1, 0.2*cm))
        date_gen = datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')
        elems.append(Paragraph(
            f'Généré par FinanceIQ le {date_gen}  ·  {nom_entreprise}  ·  {MOIS_FR[mois]} {annee}',
            s_pied
        ))

        doc.build(elems)
        return response
