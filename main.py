from Huffman_method import *

comp = Compressor()
comp.compress('/Users/andrey/PycharmProjects/Huffman_Archiver/test1', '/Users/andrey/PycharmProjects/Huffman_Archiver/test2')
decomp = Decompressor()
decomp.decompress('/Users/andrey/PycharmProjects/Huffman_Archiver/test2/test1.huff', '/Users/andrey/PycharmProjects/Huffman_Archiver/output')