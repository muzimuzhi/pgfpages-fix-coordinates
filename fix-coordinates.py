from common import *

# PyPdf2 usage intro:
#  - https://github.com/mstamy2/PyPDF2/issues/107
#  - http://www.blog.pythonlibrary.org/2018/06/07/an-intro-to-pypdf2/


def get_media_box(pdf: PdfFileReader) -> List[NumberObject]:
    page_tree: DictionaryObject = pdf.trailer["/Root"]['/Pages']
    media_box = page_tree['/MediaBox'][2:]

    return media_box


def update_page(layout, page_num):
    return page_num // (layout[0] * layout[1])


def calculate_current_layout(layout, page_num):
    h_layout = page_num % layout[0] + 1
    v_layout = page_num % layout[1] + 1

    return [h_layout, v_layout]


def update_coordinates(media_box_old, media_box_new, layout, curr_layout, coord_old):
    def size_divide(size1, size2, op=lambda x, y: x / y):
        if type(size2) in [int, float]:
            return [op(size1[0], size2), op(size1[1], size2)]
        else:
            return [op(size1[0], size2[0]), op(size1[1], size2[1])]

    page_big_size = size_divide(media_box_new, layout)
    scale = max(size_divide(media_box_old, page_big_size))
    page_small_size = size_divide(media_box_old, scale)

    in_page_offset = size_divide(page_big_size, page_small_size, lambda x, y: (x - y) / 2)
    in_split_offset = size_divide(page_big_size, curr_layout, lambda x, y: x * (y - 1))

    coord_new = size_divide(coord_old, scale)
    coord_new = size_divide(coord_new, in_page_offset, lambda x, y: x + y)
    coord_new = size_divide(coord_new, in_split_offset, lambda x, y: x + y)

    return [FloatObject(round(x, 3)) for x in coord_new]


# modified from PdfFileReader.getNamedDestinations()
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
            val = names[i + 1]
            # val = names[i+1].getObject()
            # if isinstance(val, DictionaryObject) and '/D' in val:
            #     val = val['/D']
            # dest = pdf._buildDestination(key, val)
            # if dest is not None:
            retval[key] = val

    return retval


fname = ['./latex/normal.pdf', './latex/merged.pdf']

pdf_old = PdfFileReader(fname[0])
pdf = PdfFileReader(fname[1])

media_box_old: List[NumberObject] = get_media_box(pdf_old)
media_box: List[NumberObject] = get_media_box(pdf)
layout = [2, 1]

# read from 'normal.pdf', store page2annots as list
page2annots = deque()
for page_num in range(pdf_old.getNumPages()):
    page = pdf_old.getPage(page_num)  # PyPDF2.pdf.PageObject
    if '/Annots' in page:
        curr_layout = calculate_current_layout(layout, page_num)
        for annot in page['/Annots']:
            page2annots.append([page_num, annot.getObject()])


# update coordinates of annotations
for page_num in range(pdf.getNumPages()):
    page = pdf.getPage(page_num)  # PyPDF2.pdf.PageObject
    if '/Annots' in page:
        for annot in page['/Annots']:
            annot: DictionaryObject = annot.getObject()
            # show_info(annot)

            # assume order is reserved
            page2annot = page2annots.popleft()
            assert annot == page2annot[1]
            # show_info(annot == page2annot[1])
            curr_layout = calculate_current_layout(layout, page2annot[0])

            rect: ArrayObject = annot['/Rect']
            assert len(rect) == 4, print(f'Rectangle {rect} has more coords')
            rect_old = [float(r) for r in rect]

            rect_new = update_coordinates(media_box_old, media_box, layout, curr_layout, rect_old[:2])
            rect_new.extend(update_coordinates(media_box_old, media_box, layout, curr_layout, rect_old[2:]))
            annot.update({'/Rect': ArrayObject(rect_new)})


# read from 'normal.pdf', store name2page as dict
destName2pageObj = get_named_destinations(pdf_old)
destName2normalPage: Dict[NameObject, int] = {}
for key in destName2pageObj:
    page_obj = destName2pageObj[key]
    page_num = pdf_old._getPageNumberByIndirect(page_obj)
    destName2normalPage[key] = page_num

# dests_normal: ArrayObject = pdf_old.trailer["/Root"]['/Names']['/Dests']['/Names']
# destName2normalPage: Dict[TextStringObject, int] = {}
#
# name: TextStringObject
# item: IndirectObject
# for name, item in zip(*[iter(dests_normal)] * 2):
#     dest: ArrayObject = item.getObject()  # e.g. [IndirectObject(3, 0), '/XYZ', 133.77, 667.2, NullObject]
#     show_info(name, dest)
#     print(pdf._getPageNumberByIndirect(dest[0]))
#     if NameObject('/XYZ') == dest[1]:
#         normal_page_num = pdf_old._getPageNumberByIndirect(dest[0])
#         destName2normalPage[name] = normal_page_num
#     else:
#         raise NotImplementedError(f'Destination type {dest[1]} is not implemented')

# read from and update coordinates in 'merged.pdf'
dests_merged: ArrayObject = pdf.trailer["/Root"]['/Names']['/Dests']['/Names']
for name, item in zip(*[iter(dests_merged)] * 2):
    dest: ArrayObject = item.getObject()
    if NameObject('/XYZ') == dest[1]:
        page_num = destName2normalPage[name]
        curr_layout = calculate_current_layout(layout, page_num)
        coord_old = [float(c) for c in dest[2:4]]

        coord_new = update_coordinates(media_box_old, media_box, layout, curr_layout, coord_old)
        dest[2:4] = coord_new
    else:
        raise NotImplementedError(f'Destination type {dest[1]} is not implemented')

# write to new file
fname_writer = './latex/merged-update.pdf'
pdf_writer = PdfFileWriter()

# method PdfFileWriter.cloneDocumentFromReader() is problematic,
#   see https://github.com/mstamy2/PyPDF2/issues/219
# pdf_writer.appendPagesFromReader(pdf)

# add document info
pdf_writer.cloneReaderDocumentRoot(pdf)

with open(fname_writer, 'wb') as out:
    # for page_num in range(pdf.getNumPages()):
    #     page = pdf.getPage(page_num)
    #     pdf_writer.addPage(page)

    pdf_writer.write(out)
    print('Created: {}'.format(fname_writer))
