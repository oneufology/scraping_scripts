import os
import re
import csv
import requests
from bs4 import BeautifulSoup

from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser


def main():
    r = requests.get('https://xxxxxxxxxx.com/app/abstracts/view')
    soup = BeautifulSoup(r.text, 'html.parser')

    cards = soup.find_all("div", class_="content")
    for c in cards:
        title_speaker = c.find_all("p", class_="card_cont")[0].text
        pdf_url = c.find_all("a")[0]['href']
        title, speaker = parse_title_speaker(title_speaker)
        text = get_text_from_pdf(pdf_url)
        names_l, abstract = parse_abstract(text)
        write_res_to_csv(names_l, speaker, title, abstract, pdf_url)


def parse_title_speaker(raw):
    raw = raw.replace('View pdf', '').replace('View Support Document', '')
    raw = raw.split(':', 1)[1].strip()
    spl = raw.rsplit(':', 1)
    title = spl[0].strip()
    speaker = spl[1].strip()
    return title, speaker


def get_text_from_pdf(pdf_url):
    filename = pdf_url.rsplit('/', 1)[1].replace('=', '')
    pdf = requests.get(pdf_url).content

    with open(f"{filename}.pdf", 'wb') as outf:
        outf.write(pdf)

    with open(f"{filename}.pdf", 'rb') as fp:
        parser = PDFParser(fp)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        text = ''
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)
            layout = device.get_result()
            for lt_obj in layout:
                if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
                    text += lt_obj.get_text()
        os.remove(f"{filename}.pdf")
        return text


def parse_abstract(text):
    text = re.split("AP19-\d{5}", text)[1]
    spl = text.split('Introduction :', 1)
    names = spl[0].strip()
    abstract = f"Introduction : {spl[1]}".replace('Powered by', '').strip()
    names_l = names.split('\n')
    return names_l, abstract


def write_res_to_csv(names_l, speaker, title, abstract, pdf_url):
    with open('result.csv', 'a') as outf:
        res_csv = csv.writer(outf)
        for n in names_l:
            role = 'Speaker' if n == speaker else 'Abstract author'
            row = [n, '', role, '', '', '', title, abstract, pdf_url]
            res_csv.writerow(row)


if __name__ == '__main__':
    main()