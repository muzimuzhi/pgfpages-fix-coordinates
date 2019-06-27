from common import *

# PyPdf2 usage intro:
#  - https://github.com/mstamy2/PyPDF2/issues/107
#  - http://www.blog.pythonlibrary.org/2018/06/07/an-intro-to-pypdf2/


path_to_tex = './latex/main.tex'
fname_suffix = ['normal', 'nup']
fname = [path_to_tex.replace('.tex', '-' + f + '.pdf') for f in fname_suffix]
fname_writer = fname[1].replace('.pdf', '-fixed.pdf')

LAYOUT = (2, 1)

pdf_normal = PdfFileReader(fname[0])
pdf_nup = PdfFileReader(fname[1])
pdf_writer = PdfFileWriter()


def get_media_box(pdf: PdfFileReader) -> Tuple[NumberObject]:
    page_tree: DictionaryObject = pdf.trailer["/Root"]['/Pages']
    media_box = page_tree['/MediaBox'][2:]

    return tuple(media_box)


# get media boxes
MEDIA_BOX_NORMAL: Tuple[NumberObject] = get_media_box(pdf_normal)
MEDIA_BOX_NUP: Tuple[NumberObject] = get_media_box(pdf_nup)


def update_page(layout, page_num):
    return page_num // (layout[0] * layout[1])


def calculate_current_layout(layout, page_num):
    h_layout = page_num % layout[0] + 1
    v_layout = page_num % layout[1] + 1

    return [h_layout, v_layout]


def update_coordinates(coord_old, curr_layout, layout=LAYOUT, media_old=MEDIA_BOX_NORMAL, media_new=MEDIA_BOX_NUP):
    def size_divide(size1, size2, op=lambda x, y: x / y):
        if type(size2) in [int, float]:
            return [op(size1[0], size2), op(size1[1], size2)]
        else:
            return [op(size1[0], size2[0]), op(size1[1], size2[1])]

    page_big_size = size_divide(media_new, layout)
    scale = max(size_divide(media_old, page_big_size))
    page_small_size = size_divide(media_old, scale)

    in_page_offset = size_divide(page_big_size, page_small_size, lambda x, y: (x - y) / 2)
    in_split_offset = size_divide(page_big_size, curr_layout, lambda x, y: x * (y - 1))

    coord_new = size_divide(coord_old, scale)
    coord_new = size_divide(coord_new, in_page_offset, lambda x, y: x + y)
    coord_new = size_divide(coord_new, in_split_offset, lambda x, y: x + y)

    return [FloatObject(round(x, 3)) for x in coord_new]


# based on PdfFileReader.getNamedDestinations()
def get_named_destinations(pdf: PdfFileReader, tree=None, retval=None) -> Dict[NameObject, IndirectObject]:
    """
    Retrieves the named destinations present in the document.

    :return: a dictionary which maps names to
        :class:`Destinations<PyPDF2.generic.Destination>`.
    :rtype: dict
    """
    if retval is None:
        retval = {}
        catalog = pdf.trailer["/Root"]

        # get the name tree
        if "/Dests" in catalog:
            tree = catalog["/Dests"]
        elif "/Names" in catalog:
            names = catalog['/Names']
            if "/Dests" in names:
                tree = names['/Dests']

    if tree is None:
        return retval

    if "/Kids" in tree:
        # recurse down the tree
        for kid in tree["/Kids"]:
            pdf.getNamedDestinations(kid.getObject(), retval)

    if "/Names" in tree:
        names = tree["/Names"]
        for i in range(0, len(names), 2):
            key = names[i].getObject()
            val = names[i + 1]  # modified here
            retval[key] = val

    return retval


def get_page2annots(pdf: PdfFileReader) -> Deque:
    """
    Return list of (page_num, annot_obj) pairs.
    """
    page2annots = deque()

    for page_num in range(pdf.getNumPages()):
        page = pdf.getPage(page_num)  # page: PyPDF2.pdf.PageObject
        if '/Annots' in page:
            for annot in page['/Annots']:
                page2annots.append([page_num, annot.getObject()])

    return page2annots


def set_annotations(pdf: PdfFileReader, page2annots: Deque) -> None:
    # update coordinates of annotations
    for page_num in range(pdf.getNumPages()):
        page = pdf.getPage(page_num)  # PyPDF2.pdf.PageObject
        if '/Annots' in page:
            for annot in page['/Annots']:
                annot: DictionaryObject = annot.getObject()

                # assume order is reserved
                page2annot = page2annots.popleft()
                assert annot == page2annot[1]
                curr_layout = calculate_current_layout(LAYOUT, page2annot[0])

                rect: ArrayObject = annot['/Rect']
                assert len(rect) == 4, print(f'Rectangle {rect} has more coords')
                rect_old = [float(r) for r in rect]

                rect_new = update_coordinates(rect_old[:2], curr_layout)
                rect_new.extend(update_coordinates(rect_old[2:], curr_layout))
                annot.update({'/Rect': ArrayObject(rect_new)})


def get_name2page(pdf: PdfFileReader) -> Dict[NameObject, int]:
    name2page_obj = get_named_destinations(pdf)

    name2page: Dict[NameObject, int] = {}
    for key in name2page_obj:
        page_obj = name2page_obj[key]
        page_num = pdf._getPageNumberByIndirect(page_obj)
        name2page[key] = page_num

    return name2page


def set_named_destinations(pdf: PdfFileReader, name2page: Dict[NameObject, int]) -> None:
    dests_merged: ArrayObject = pdf.trailer["/Root"]['/Names']['/Dests']['/Names']

    for name, item in zip(*[iter(dests_merged)] * 2):
        dest: ArrayObject = item.getObject()
        if NameObject('/XYZ') == dest[1]:
            page_num = name2page[name]
            curr_layout = calculate_current_layout(LAYOUT, page_num)
            coord_old = [float(c) for c in dest[2:4]]

            coord_new = update_coordinates(coord_old, curr_layout)
            dest[2:4] = coord_new
        else:
            raise NotImplementedError(f'Destination type {dest[1]} is not implemented')


# update coordinates of annotations
normalPage2annots = get_page2annots(pdf_normal)
set_annotations(pdf_nup, normalPage2annots)

# update coordinates of named destinations
destName2normalPage = get_name2page(pdf_normal)
set_named_destinations(pdf_nup, destName2normalPage)

# write to new file
pdf_writer.cloneReaderDocumentRoot(pdf_nup)

# method PdfFileWriter.cloneDocumentFromReader() is problematic,
#   see https://github.com/mstamy2/PyPDF2/issues/219
#
# pdf_writer.appendPagesFromReader(pdf_nup)

with open(fname_writer, 'wb') as out:
    pdf_writer.write(out)
    print('Created: {}'.format(fname_writer))
