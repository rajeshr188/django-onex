import io
from io import BytesIO
from itertools import groupby

from num2words import num2words
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape, letter, mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    Flowable,
    Frame,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.doctemplate import PageTemplate
from reportlab.rl_config import defaultPageSize

from contact.models import Customer
from girvi.models import Loan

PAGESIZE = (140 * mm, 216 * mm)
BASE_MARGIN = 5 * mm


class PdfCreator:
    def add_page_number(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Times-Roman", 10)
        page_number_text = "%d" % (doc.page)
        canvas.drawCentredString(0.75 * inch, 0.75 * inch, page_number_text)
        canvas.restoreState()

    def get_body_style(self):
        sample_style_sheet = getSampleStyleSheet()
        body_style = sample_style_sheet["BodyText"]
        body_style.fontSize = 18
        return body_style

    def build_pdf(self):
        pdf_buffer = BytesIO()
        my_doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=PAGESIZE,
            topMargin=BASE_MARGIN,
            leftMargin=BASE_MARGIN,
            rightMargin=BASE_MARGIN,
            bottomMargin=BASE_MARGIN,
        )
        body_style = self.get_body_style()
        flowables = [
            Paragraph("First paragraph", body_style),
            Paragraph("Second paragraph", body_style),
        ]
        my_doc.build(
            flowables,
            onFirstPage=self.add_page_number,
            onLaterPages=self.add_page_number,
        )
        pdf_value = pdf_buffer.getvalue()
        pdf_buffer.close()
        return pdf_value


class CentreLine(Flowable):
    """
    Draws a dotted line in the centre of the page vertically to tear along
    """

    def __init__(self):
        Flowable.__init__(self)

    def draw(self):
        # Set the line width and style
        self.canv.setLineWidth(0.5)
        self.canv.setDash(1, 3)  # 1pt on, 3pt off

        # Calculate the center of the page
        center_x = landscape(A4)[0] / 2
        center_y = landscape(A4)[1] / 2

        # Draw the dotted line from top to bottom at the center of the page
        self.canv.line(center_x, landscape(A4)[1], center_x, 0)


class BoxyLine(Flowable):
    """
    Draw a box + line + text

    -----------------------------------------
    | foobar |
    ---------

    """

    def __init__(self, x=0, y=-15, width=40, height=15, text=""):
        Flowable.__init__(self)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

    def draw(self):
        """
        Draw the shape, text, etc
        """
        # self.canv.rect(self.x, self.y, self.width, self.height)
        self.canv.line(self.x, 0, 350, 0)
        self.canv.drawString(self.x + 5, self.y + 3, self.text)


def get_loan_pdf(loan):
    pdfmetrics.registerFont(
        TTFont("NotoSansTamil-Regular", "static/fonts/NotoSansTamil-Regular.ttf")
    )
    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()
    my_canvas = Canvas(buffer, pagesize=landscape(A4))
    w, h = my_canvas._pagesize
    spacer = Spacer(0, 0.25 * inch)

    # Define styles for the paragraphs
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    heading = styles["Heading1"]
    normal.alignment = TA_JUSTIFY

    # Define the text for the paragraphs

    shop = """<font color=blue size=14>J Champalal</font> <br />
                <font size = 10 >Pawn Brokers</font>
                no:8, Lathid sahib street,<br />
                R.N Palayam,Vellore<br/>
                Phone:2416-2232536"""
    customer = f"""
                    {loan.customer.name} {loan.customer.relatedas} {loan.customer.relatedto}<br/>
                    {loan.customer.Address}<br />
                    {loan.customer.area}
                    vellore,632001<br />
                    ph:{loan.customer.contactno}
                    """

    # Create the Paragraph objects
    logo = Image("static/images/falconx.png", 50, 50)
    # print(loan.customer)
    # customer_img = Image(loan.customer.pic.url,50,50)

    simple_tblstyle = TableStyle(
        [
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
        ]
    )

    header = Table(
        [
            [
                Paragraph("Sec Rules 8"),
                Paragraph(
                    "Pawn Ticket <font size = 14 name='NotoSansTamil-Regular'>அடகு சீட்டு   </font>"
                ),
                Paragraph("PBL NO:1515/2017"),
            ]
        ]
    )
    # table1.setStyle(simple_tblstyle)
    shop = Table(
        [
            [logo, Paragraph(shop, normal)],
        ]
    )
    loanid_date = Table(
        [
            [
                Paragraph(f"LoanID : {loan.loanid}"),
                Paragraph(f"Date: {loan.created.date()}"),
            ]
        ]
    )
    loanid_date.setStyle(simple_tblstyle)
    loanitems = Table(
        [
            [
                ListFlowable(
                    [
                        # ListItem(Paragraph('Paragraph #2', normal),
                        #         bulletColor="blue",),
                        Paragraph(f"{loan.itemdesc}", normal),
                    ]
                )
            ]
        ]
    )
    loanitems.setStyle(simple_tblstyle)
    loanitem_details = Table(
        [
            [
                Paragraph(f"Gross Wt: {loan.itemweight} gms"),
                Paragraph("Nett Wt: 100.00"),
                Paragraph(f"Value: {loan.itemvalue}"),
            ]
        ]
    )
    loanitem_details.setStyle(simple_tblstyle)
    amount_tbl = Table(
        [
            [
                Paragraph(f"Loan Amount: {loan.loanamount}"),
                Paragraph(
                    f"Loan Amount In Words<br/>{num2words(loan.loanamount, lang='en_IN')}"
                ),
            ],
        ]
    )
    amount_tbl.setStyle(simple_tblstyle)
    terms = Table(
        [
            [
                ListFlowable(
                    [
                        Paragraph(
                            "Time agreed for redemption of articles is 3 months.",
                            normal,
                        ),
                        Paragraph("Above mentioned articles are my own"),
                        # ListItem(Paragraph('Paragraph #2', normal),
                        #          bulletColor="blue",),
                    ]
                )
            ]
        ]
    )
    terms.setStyle(simple_tblstyle)
    signature = Table(
        [
            ["", ""],
            [
                Paragraph(
                    "<font size=8 >Signature/Thumb Impression of the pawner</font>"
                ),
                Paragraph(
                    "<font size=8 >Signature of the Pawn broker/his Agent</font>"
                ),
            ],
        ]
    )
    signature.setStyle(simple_tblstyle)

    flowables = [header]
    # flowables.append(CentreLine())
    flowables.append(shop)
    flowables.append(spacer)
    flowables.append(loanid_date)
    flowables.append(BoxyLine(text="Customer"))
    flowables.append(spacer)
    flowables.append(
        Table(
            [
                [logo, Paragraph(customer, normal)],
            ]
        )
    )
    flowables.append(BoxyLine(text="Following article/s are pawned with me:"))
    flowables.append(spacer)
    flowables.append(loanitems)
    flowables.append(loanitem_details)
    flowables.append(amount_tbl)

    flowables.append(BoxyLine(text="Terms & Conditions"))
    flowables.append(spacer)
    flowables.append(terms)
    flowables.append(Paragraph("  My monthly income is above Rs:"))
    flowables.append(spacer)
    flowables.append(signature)

    right_flowables = [*flowables]
    right_flowables.append(spacer)

    right_flowables.append(
        Table(
            [
                [loan.loanid, loan.created.date()],
                [loan.loanamount, loan.itemweight],
                [loan.customer.name, loan.itemdesc],
            ]
        )
    )

    # right_flowables.append(Paragraph('ipsum lorem', normal))

    left_frame = Frame(
        10 * mm, 10 * mm, width=(w - 30 * mm) / 2, height=h - 20 * mm, showBoundary=1
    )
    right_frame = Frame(
        (w + 10 * mm) / 2,
        10 * mm,
        width=(w - 30 * mm) / 2,
        height=h - 20 * mm,
        showBoundary=1,
    )

    left_frame.addFromList(flowables, my_canvas)
    right_frame.addFromList(right_flowables, my_canvas)

    # Set the line width and style
    my_canvas.setLineWidth(0.5)
    my_canvas.setDash(1, 3)  # 1pt on, 3pt off

    # Calculate the center of the page
    center_x = landscape(A4)[0] / 2
    center_y = landscape(A4)[1] / 2

    # Draw the dotted line from top to bottom at the center of the page
    my_canvas.line(center_x, landscape(A4)[1], center_x, 0)
    my_canvas.line(w / 2, 100, w, 100)

    my_canvas.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def get_notice_pdf(selection=None):
    # TODO: paginate the pdf for better performance
    # TODO: add a progress bar
    # TODO: add page templates

    # # get all loans with selected ids
    selected_loans = selection
    # get a list of unique customers for the selected loans
    customers = (
        Customer.objects.filter(loan__in=selected_loans)
        .select_related("loan")
        .distinct()
    )

    grouped_loans = groupby(selected_loans, lambda loan: loan.customer)
    print(f"customers gathered:{customers.count()}")
    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()
    # Create the PDF object, using the buffer as its "file."
    doc = SimpleDocTemplate(buffer)
    doc.title = "Notice-Group"
    # Define styles for the paragraphs
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Normal_CENTER",
            parent=styles["Normal"],
            fontName="Helvetica",
            wordWrap="LTR",
            alignment=TA_CENTER,
            fontSize=12,
            leading=13,
            textColor=colors.black,
            borderPadding=0,
            leftIndent=0,
            rightIndent=0,
            spaceAfter=0,
            spaceBefore=0,
            splitLongWords=True,
            spaceShrinkage=0.05,
        )
    )
    top = styles["Normal_CENTER"]
    normal = styles["Normal"]
    title = styles["Title"]
    heading = styles["Heading1"]
    story = []
    pages = []
    spacer = Spacer(0, 0.25 * inch)
    simple_tblstyle = TableStyle(
        [
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
        ]
    )

    for customer, loans in grouped_loans:
        # loans = list(loans) :Use generators instead of lists:
        loans = (loan for loan in loans)
        story.append(spacer)
        story.append(Paragraph("TAMILNADU PAWNBROKERS ACT, 1943", top))
        story.append(spacer)
        story.append(Paragraph("NOTICE TO REDEEM PLEDGE", heading))
        story.append(spacer)
        story.append(
            Paragraph(
                f"""
            To,<br/>
            {customer.name} {customer.relatedas} {customer.relatedto}<br/>
            {customer.Address}<br/>
            {customer.area}<br/>
            {customer.contactno}""",
                normal,
            )
        )
        story.append(spacer)
        story.append(
            Paragraph(
                """
        Notice is hereby given that the Pledge of the following article(s) is now <br/>
        at the Pawn Broker named below, and that unless the same is redeemed within<br/>
        30 days from the date hereof, it will be sold by public auction at the Pawn<br/>
        Broker's place of business, without further notice to the Pledger or his agent.<br/>
        """
            )
        )
        story.append(spacer)
        story.append(
            Paragraph(
                f"""
        Name of Pawn Broker:J Champalal Pawn Brokers
                """,
                normal,
            )
        )
        story.append(Paragraph("Description of Articles Pledged:"))
        width = 400
        height = 100
        x = 100
        y = 300
        f = Table(
            [
                [item.loanid, item.itemweight, item.created, item.itemdesc]
                for item in loans
            ]
        )

        f.setStyle(simple_tblstyle)
        story.append(spacer)
        story.append(f)
        story.append(PageBreak())

    print("pdf generated")
    # Save the PDF and return the response
    print(f"story length: {len(story)}")
    doc.build([KeepTogether(story)])
    print("doc built")
    pdf = buffer.getvalue()
    print("pdf ready")
    buffer.close()
    print(f"pdf length: {pdf.__sizeof__()}")
    return pdf


# copilot implementation
# from reportlab.lib.pagesizes import landscape, A4
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib.units import inch
# from reportlab.lib import colors
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
# from reportlab.pdfgen import canvas
# import io

# def get_notice_pdf(selection=None):
#     # TODO: paginate the pdf for better performance
#     # TODO: add a progress bar
#     # TODO: add page templates

#     # # get all loans with selected ids
#     selected_loans = selection
#     # get a list of unique customers for the selected loans
#     customers = (
#         Customer.objects.filter(loan__in=selected_loans)
#         .select_related("loan")
#         .distinct()
#     )

#     grouped_loans = groupby(selected_loans, lambda loan: loan.customer)
#     print(f"customers gathered:{customers.count()}")

#     # Create the PDF object, using the buffer as its "file."
#     buffer = io.BytesIO()
#     doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
#     doc.title = "Notice-Group"

#     # Define styles for the paragraphs
#     styles = getSampleStyleSheet()
#     styles.add(
#         ParagraphStyle(
#             name="Normal_CENTER",
#             parent=styles["Normal"],
#             fontName="Helvetica",
#             wordWrap="LTR",
#             alignment=canvas.Canvas.TA_CENTER,
#             fontSize=12,
#             leading=13,
#             textColor=colors.black,
#             borderPadding=0,
#             leftIndent=0,
#             rightIndent=0,
#             spaceAfter=0,
#             spaceBefore=0,
#             splitLongWords=True,
#             spaceShrinkage=0.05,
#         )
#     )
#     top = styles["Normal_CENTER"]
#     normal = styles["Normal"]
#     title = styles["Title"]
#     heading = styles["Heading1"]

#     # Create the canvas
#     canvas_obj = canvas.Canvas(buffer, pagesize=landscape(A4))

#     for customer, loans in grouped_loans:
#         # loans = list(loans) :Use generators instead of lists:
#         loans = (loan for loan in loans)

#         # Create a new page
#         canvas_obj.showPage()

#         # Add the customer information
#         canvas_obj.setFont("Helvetica", 12)
#         canvas_obj.drawCentredString(300, 700, "TAMILNADU PAWNBROKERS ACT, 1943")
#         canvas_obj.drawCentredString(300, 650, "NOTICE TO REDEEM PLEDGE")
#         canvas_obj.drawCentredString(
#             300, 600, f"{customer.name} {customer.relatedas} {customer.relatedto}"
#         )
#         canvas_obj.drawCentredString(300, 575, customer.Address)
#         canvas_obj.drawCentredString(300, 550, customer.area)
#         canvas_obj.drawCentredString(300, 525, customer.contactno)

#         # Add the notice to redeem pledge
#         canvas_obj.setFont("Helvetica-Bold", 12)
#         canvas_obj.drawString(50, 450, "Notice is hereby given that the Pledge of the following article(s) is now")
#         canvas_obj.drawString(50, 435, "at the Pawn Broker named below, and that unless the same is redeemed within")
#         canvas_obj.drawString(50, 420, "30 days from the date hereof, it will be sold by public auction at the Pawn")
#         canvas_obj.drawString(50, 405, "Broker's place of business, without further notice to the Pledger or his agent.")

#         # Add the pawn broker information
#         canvas_obj.setFont("Helvetica", 12)
#         canvas_obj.drawString(50, 375, "Name of Pawn Broker:J Champalal Pawn Brokers")

#         # Add the table of pawned items
#         data = [
#             ["Loan ID", "Item Weight", "Created", "Item Description"],
#             *[list(map(str, [item.loanid, item.itemweight, item.created, item.itemdesc])) for item in loans]
#         ]
#         table = Table(data)
#         table.setStyle(TableStyle([
#             ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
#             ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
#         ]))
#         table.wrapOn(canvas_obj, 0, 0)
#         table.drawOn(canvas_obj, 50, 300)

#     # Save the PDF and return the response
#     canvas_obj.save()
#     pdf = buffer.getvalue()
#     buffer.close()
#     return pdf


def print_noticegroup(selection=None):
    pdf = get_notice_pdf(selection)
    response = HttpResponse(pdf, content_type="application/pdf")
    filename = "Notice-Group.pdf"
    content = "inline; filename='%s'" % (filename)
    download = request.GET.get("download")
    if download:
        content = "attachment; filename='%s'" % (filename)
    response["Content-Disposition"] = content
    return response
