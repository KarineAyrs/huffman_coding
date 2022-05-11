import collections
import argparse
import time
import sys
import pickle


class Node:
    def __init__(self, symbol=None, proba=None, code='', left=None, right=None):
        self.symbol = symbol
        self.proba = proba
        self.code = code
        self.left = left
        self.right = right

    def __repr__(self):
        return f'{str(self.symbol)} : {str(self.proba)}'


class Huffman:
    def __init__(self):
        self.__enc_root = None
        self.__encode_table = None
        self.__enc_file_name = None
        self.__dec_file_name = None
        self.__decode_table = None
        self.__dec_root = None
        self.__file = None

    def encode(self, enc_file_name):
        self.__enc_file_name = enc_file_name
        self.__build_tree_encode()
        self.__encode_table = {}
        self.__build_table_encode()
        self.__code()

    def decode(self, dec_file_name):
        self.__dec_file_name = dec_file_name
        ext, encoding = self.__get_aux_decode()
        self.__build_tree_decode()
        self.__decode(encoding, ext)

    def __decode(self, encoding, ext):
        root = self.__dec_root
        res = []
        curr = root
        for i in range(len(encoding)):
            code = encoding[i]

            if code == '0':
                curr = curr.left

            elif code == '1':
                curr = curr.right

            if curr.left is None and curr.right is None:
                res.append(curr.symbol)
                curr = root

        with open(self.__dec_file_name.split('.')[0] + '_dec.' + ext, 'wb') as f:
            f.write(bytearray(res))

    def __get_aux_decode(self):
        ext = ''
        encoding = ''
        code_l = 0

        if self.__dec_file_name.split('.')[-1] != 'zmh':
            sys.exit('wrong format!')

        res = b''
        with open(self.__dec_file_name, 'rb') as f:
            i = 0
            for l in f:
                if i == 0:
                    try:
                        code_l = int(l.decode(encoding='utf-8').split('\n')[0])
                    except:
                        sys.exit('Damaged archive')

                elif i == 1:
                    ext = l.decode(encoding='utf-8').split('\n')[0]
                    if len(ext) > 5:
                        sys.exit('Damaged archive')

                else:
                    res += l

                i += 1

        len_dic = int.from_bytes(res[:4], 'big')
        table_h = pickle.loads(res[4:len_dic + 4])
        bitecode = res[len_dic + 5:]

        last_zeros = code_l - (code_l // 8) * 8

        for i in range(len(bitecode)):
            # обработка последнего байта
            if i >= len(bitecode) - 1:
                encoding += bin(int.from_bytes(bitecode[i:], 'big'))[2:].zfill(last_zeros)
            else:
                encoding += bin(int.from_bytes(bitecode[i:i + 1], 'big'))[2:].zfill(8)

        self.__decode_table = table_h
        return ext, encoding

    def __build_tree_encode(self):

        f_open = open(self.__enc_file_name, 'rb')
        self.__file = f_open.read()
        f_open.close()
        syms = [s for s in self.__file]
        freq_dict = dict(collections.Counter(syms))

        print('original size (bites): ', len(syms))

        _List = [Node(symbol=k, proba=v) for k, v in freq_dict.items()]

        while len(_List) != 1:
            _List.sort(key=lambda node: node.proba, reverse=True)

            p1 = _List.pop(-1)
            p2 = _List.pop(-1)

            p1.code = '0'
            p2.code = '1'

            new_node = Node(p1.symbol + p2.symbol, p1.proba + p2.proba, left=p1, right=p2)

            _List.append(new_node)

        self.__enc_root = _List[0]

    def __build_table_encode(self):

        q = [[self.__enc_root, 0]]  # 0 -пустая, 1 - посетили
        code = ''
        table = {}
        while len(q) != 0:
            v = q[-1]

            if v[1] == 1:
                code = code[:-1]  # подъем по дереву вверх
                q.remove(v)
                continue

            if v[1] == 0:
                v[1] = 1

            if v[0].code is not None:
                code += v[0].code  # спуск вниз по дереву

            if v[0].left is not None and v[0].right is not None:
                q.append([v[0].right, 0])
                q.append([v[0].left, 0])

            else:
                table.update({v[0].symbol: code})
                q.remove(v)
                code = code[:-1]  # подъем по дереву вверх

        self.__encode_table = table

    def __build_tree_decode(self):

        root = Node('root', None)
        j = 1
        for k, v in self.__decode_table.items():
            curr = root
            for i in range(len(v)):
                code = v[i]
                symb = k if i == len(v) - 1 else 'v' + str(j)
                if code == '0':
                    if curr.left is None:
                        curr.left = Node(code=v[i], symbol=symb)
                        j += 1
                    curr = curr.left
                elif code == '1':
                    if curr.right is None:
                        curr.right = Node(code=v[i], symbol=symb)
                        j += 1
                    curr = curr.right

        self.__dec_root = root

    def __code(self):
        old_ext = self.__enc_file_name.split('.')[-1]
        res = ''.join([self.__encode_table[sym] for sym in self.__file])
        res_bytes = b''.join([int(res[i:8 + i], 2).to_bytes(1, 'big') for i in range(0, len(res), 8)])

        print('size after compress (bites, raw): ', len(res_bytes))

        with open(self.__enc_file_name.split('.')[0] + '.zmh', 'wb') as r_f:
            r_f.write((str(len(res)) + '\n').encode('utf-8'))
            r_f.write((old_ext + '\n').encode('utf-8'))
            d = pickle.dumps(self.__encode_table)
            r_f.write(len(d).to_bytes(4, 'big'))
            r_f.write(d)

            r_f.write('\n'.encode('utf-8'))
            r_f.write(bytes(res_bytes))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Welcome to ZipMeHuffman!')
    parser.add_argument('--r', action='store', choices=['1', '2'], dest='regime', help='1 - compress, 2-decompress',
                        required=True)
    parser.add_argument('--f', action='store', dest='filename', required=True,
                        help='path to file to compress/decompress')

    args = parser.parse_args()

    filename, regime = args.filename, args.regime
    start = time.time()
    huffman = Huffman()

    if regime == '1':
        print(f'compressing file {filename}...')
        huffman.encode(filename)
    if regime == '2':
        print(f'decompressing file {filename}...')
        huffman.decode(filename)

    print('time in seconds: ', time.time() - start)
