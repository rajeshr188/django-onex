import io
from io import BytesIO
from itertools import groupby

from django.db.models import Count
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
from reportlab.platypus import (Flowable, Frame, Image, KeepTogether,
                                ListFlowable, ListItem, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)
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
                Paragraph("Sec Rules 8", styles["Normal"]),
                Paragraph(
                    "Pawn Ticket <font size = 14 name='NotoSansTamil-Regular'>அடகு சீட்டு   </font>",
                    styles["Heading3"],
                ),
                Paragraph("PBL NO:1515/2017", styles["Normal"]),
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
                Paragraph(f"LoanID : {loan.loan_id}"),
                Paragraph(f"Date: {loan.loan_date.date()}"),
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
                        Paragraph(f"{loan.item_desc}", normal),
                    ]
                )
            ]
        ]
    )
    result = []
    for item in loan.get_weight:
        item_type = item["itemtype"]
        total_weight_purity = item["total_weight"]
        result.append(f"{item_type}:{total_weight_purity}")

    # Join the results into a single string
    weight = " ".join(result)
    result = []
    for item in loan.get_pure:
        item_type = item["itemtype"]
        total_weight_purity = round(item["pure_weight"])
        result.append(f"{item_type}:{total_weight_purity}")
    # Join the results into a single string
    pure = " ".join(result)
    loanitems.setStyle(simple_tblstyle)
    loanitem_details = Table(
        [
            [
                Paragraph(f"Gross Wt: {weight} "),
                Paragraph(f"Nett Wt: {pure}"),
                Paragraph(f"Value: {loan.current_value()}"),
            ]
        ]
    )
    loanitem_details.setStyle(simple_tblstyle)
    amount_tbl = Table(
        [
            [
                Paragraph(f"Loan Amount: {loan.loan_amount}"),
                Paragraph(f"{num2words(loan.loan_amount, lang='en_IN')} rupees only"),
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
                [loan.loan_id, loan.loan_date.date()],
                [loan.loan_amount, weight],
                [loan.customer.name, loan.item_desc],
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
    my_canvas.line(w / 2, 110, w, 110)

    my_canvas.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def on_all_pages(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 10)
    canvas.drawString(inch, 0.75 * inch, "Page %d" % doc.page)
    canvas.restoreState()


def get_notice_pdf(selection=None):
    # TODO: paginate the pdf for better performance
    # TODO: add a progress bar
    # TODO: add page templates

    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()
    # Create the PDF object, using the buffer as its "file."
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    doc.title = "Notice-Group"

    # Define styles for the paragraphs
    styles = getSampleStyleSheet()
    top_style = ParagraphStyle(
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

    # Main story list
    story = []
    spacer = Spacer(0, 0.25 * inch)
    simple_tblstyle = TableStyle(
        [
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
        ]
    )

    # Iterate over selected loans
    for customer, loans in groupby(selection, key=lambda x: x.customer):
        # Grouped loans
        loans = list(loans)

        # Append paragraphs to the story
        story.extend(
            [
                spacer,
                Paragraph("TAMILNADU PAWNBROKERS ACT, 1943", top_style),
                spacer,
                Paragraph("NOTICE TO REDEEM PLEDGE", styles["Heading1"]),
                spacer,
                Paragraph(f"To,<br/>{customer}", styles["Normal"]),
                spacer,
                Paragraph(
                    "Notice is hereby given that the Pledge of the following article(s) is now "
                    "at the Pawn Broker named below, and that unless the same is redeemed within "
                    "30 days from the date hereof, it will be sold by public auction at the Pawn "
                    "Broker's place of business, without further notice to the Pledger or his agent."
                ),
                spacer,
                Paragraph(
                    "<br/>Name of Pawn Broker: J Champalal Pawn Brokers",
                    styles["Normal"],
                ),
                Paragraph("<br/>Description of Articles Pledged:", styles["Normal"]),
            ]
        )

        # Create table
        table_data = [["#", "Loan ID", "Created", "Item Weight", "Item Description"]]
        table_data.extend(
            [
                [
                    i + 1,
                    loan.loan_id,
                    loan.loan_date.date(),
                    loan.get_weight[0],
                    item.itemdesc,
                ]
                for i, (loan, item) in enumerate(
                    ((loan, item) for loan in loans for item in loan.loanitems.all())
                )
            ]
        )

        # Add table to the story
        f = Table(table_data)
        f.setStyle(simple_tblstyle)
        story.extend([spacer, f, PageBreak()])

    # Save the PDF and return the response
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


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
