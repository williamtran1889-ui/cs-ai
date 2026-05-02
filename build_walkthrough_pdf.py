"""Build colab_walkthrough.pdf from the step-by-step Colab guide."""

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Preformatted,
    PageBreak,
)

OUTPUT = "colab_walkthrough.pdf"

styles = getSampleStyleSheet()
title = ParagraphStyle(
    "Title", parent=styles["Title"], fontSize=20, spaceAfter=14, alignment=TA_LEFT
)
h1 = ParagraphStyle(
    "H1",
    parent=styles["Heading1"],
    fontSize=14,
    spaceBefore=14,
    spaceAfter=6,
    textColor=HexColor("#1a1a1a"),
)
body = ParagraphStyle(
    "Body", parent=styles["BodyText"], fontSize=10.5, leading=14, spaceAfter=6
)
note = ParagraphStyle(
    "Note", parent=body, textColor=HexColor("#555555"), fontSize=9.5, leading=13
)
code = ParagraphStyle(
    "Code",
    parent=styles["Code"],
    fontName="Courier",
    fontSize=9,
    leading=11,
    leftIndent=10,
    backColor=HexColor("#f4f4f4"),
    borderPadding=6,
    spaceBefore=4,
    spaceAfter=8,
)


def p(text):
    return Paragraph(text, body)


def n(text):
    return Paragraph(text, note)


def head(text):
    return Paragraph(text, h1)


def block(text):
    return Preformatted(text, code)


story = [
    Paragraph("Run the HAR LSTM/CNN script in Google Colab", title),
    n(
        "Step-by-step walkthrough for running <b>har_lstm_cnn.py</b> on the "
        "UCI HAR dataset using a Google Colab notebook. Each numbered step "
        "is one thing to do; each gray block goes in its own Colab cell."
    ),
    Spacer(1, 0.1 * inch),

    head("1. Open Colab and create a notebook"),
    p("Go to <b>colab.research.google.com</b>, then File &rarr; New notebook."),

    head("2. (Optional) Switch to GPU"),
    p(
        "Runtime &rarr; Change runtime type &rarr; Hardware accelerator: "
        "<b>T4 GPU</b> &rarr; Save."
    ),
    n(
        "Not required &mdash; the script finishes on CPU in a few minutes &mdash; "
        "but the free GPU is faster."
    ),

    head("3. Download the UCI HAR dataset"),
    p("Paste in a new cell and run:"),
    block(
        '!wget -q "https://archive.ics.uci.edu/static/public/240/human+activity+recognition+using+smartphones.zip" -O har.zip\n'
        '!unzip -q -o har.zip\n'
        '!ls'
    ),
    n("If ls shows UCI HAR Dataset.zip (an inner zip), run this in a second cell:"),
    block(
        '!unzip -q -o "UCI HAR Dataset.zip"\n'
        '!ls "UCI HAR Dataset"'
    ),
    p(
        "You should see <b>train</b>, <b>test</b>, <b>features.txt</b>, etc. "
        "listed. If <i>ls</i> shows that, the data is in place."
    ),

    head("4. Get the training script"),
    p("Pick whichever option matches your situation:"),
    p("<b>(a) If the GitHub repo is public</b> &mdash; clone it:"),
    block(
        "!git clone https://github.com/williamtran1889-ui/cs-ai.git\n"
        "!cp cs-ai/har_lstm_cnn.py ."
    ),
    p("<b>(b) If the repo is private</b> &mdash; upload from your computer:"),
    block(
        "from google.colab import files\n"
        'files.upload()   # click "Choose Files" and pick har_lstm_cnn.py'
    ),
    p(
        "<b>(c) Paste the script directly</b> &mdash; open the file on GitHub, "
        'click "Raw", copy all the text, then in Colab do '
        "File &rarr; New file &rarr; name it <b>har_lstm_cnn.py</b> &rarr; "
        "paste &rarr; save."
    ),
    p(
        "After this step, run <b>!ls</b> in a cell. You should see both "
        "<b>har_lstm_cnn.py</b> and <b>UCI HAR Dataset/</b> in the same "
        "directory (<i>/content</i>)."
    ),

    head("5. Confirm dependencies"),
    n("Colab has them preinstalled &mdash; this is just a sanity check."),
    block(
        "import tensorflow, keras, sklearn, numpy\n"
        'print("tf", tensorflow.__version__, "| keras", keras.__version__,\n'
        '      "| sklearn", sklearn.__version__, "| numpy", numpy.__version__)'
    ),
    p("If this runs without error, you're good."),

    head("6. Run the script"),
    block("!python har_lstm_cnn.py"),
    p(
        "Expect 30 epochs of LSTM training, then 30 epochs of CNN training, "
        "then two evaluation blocks (loss, accuracy, per-class F1, "
        "classification report, confusion matrix). On free T4 it's roughly "
        "1-3 minutes total; CPU-only is about 5-10 minutes."
    ),

    head("7. (Optional) Save the output"),
    p("To capture the printed output to a file you can download:"),
    block(
        "!python har_lstm_cnn.py 2>&1 | tee results.txt\n"
        "from google.colab import files\n"
        'files.download("results.txt")'
    ),

    head("Common things that go wrong"),
    p(
        "<b>FileNotFoundError: 'UCI HAR Dataset'</b> &rarr; the dataset folder "
        "isn't in the same directory as the script. Run <b>!ls</b> and "
        "<b>!pwd</b> to check; if needed, <b>%cd /content</b>."
    ),
    p(
        "<b>No module named 'flax'</b> (only if you're running an old version "
        "of the script) &rarr; make sure you have the latest from the "
        "<b>claude/har-lstm-cnn-models-n8e7Q</b> branch &mdash; that import "
        "was removed."
    ),
    p(
        "<b>Session timed out mid-training</b> &rarr; Colab's free tier "
        "disconnects after ~90 min idle. Just rerun the cells; nothing "
        "persists between sessions anyway, so you'll redo steps 3-6."
    ),
]

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=LETTER,
    leftMargin=0.9 * inch,
    rightMargin=0.9 * inch,
    topMargin=0.9 * inch,
    bottomMargin=0.9 * inch,
    title="Run the HAR LSTM/CNN script in Google Colab",
)
doc.build(story)
print(f"wrote {OUTPUT}")
