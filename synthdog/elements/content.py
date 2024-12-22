"""
Donut
Copyright (c) 2022-present NAVER Corp.
MIT License
"""
from collections import OrderedDict

import numpy as np
from synthtiger import components

from elements.textbox import TextBox
from layouts import GridStack


class TextReader:
    def __init__(self, path, cache_size=2 ** 28, block_size=2 ** 20):
        self.fp = open(path, "r", encoding="utf-8")
        self.length = 0
        self.offsets = [0]
        self.cache = OrderedDict()
        self.cache_size = cache_size
        self.block_size = block_size
        self.bucket_size = cache_size // block_size
        self.idx = 0

        while True:
            text = self.fp.read(self.block_size)
            if not text:
                break
            self.length += len(text)
            self.offsets.append(self.fp.tell())

    def __len__(self):
        return self.length

    def __iter__(self):
        return self

    def __next__(self):
        char = self.get()
        self.next()
        return char

    def move(self, idx):
        self.idx = idx

    def next(self):
        self.idx = (self.idx + 1) % self.length

    def prev(self):
        self.idx = (self.idx - 1) % self.length

    def get(self):
        key = self.idx // self.block_size

        if key in self.cache:
            text = self.cache[key]
        else:
            if len(self.cache) >= self.bucket_size:
                self.cache.popitem(last=False)

            offset = self.offsets[key]
            self.fp.seek(offset, 0)
            text = self.fp.read(self.block_size)
            self.cache[key] = text

        self.cache.move_to_end(key)
        char = text[self.idx % self.block_size]
        return char
    
    def move_to_line_by_random_position(self):

        random_position = np.random.randint(self.length)  
        self.fp.seek(random_position, 0) 

        # 向前扫描找到行头
        while random_position > 0:
            self.fp.seek(random_position - 1, 0)
            char = self.fp.read(1)
            if char == '\n': 
                break
            random_position -= 1
        self.idx = random_position


class Content:
    def __init__(self, config):
        self.margin = config.get("margin", [0, 0.1])
        self.reader = TextReader(**config.get("text", {}))
        self.font = components.BaseFont(**config.get("font", {}))
        self.layout = GridStack(config.get("layout", {}))
        self.textbox = TextBox(config.get("textbox", {}))
        self.textbox_color = components.Switch(components.Gray(), **config.get("textbox_color", {}))
        self.content_color = components.Switch(components.Gray(), **config.get("content_color", {}))

    def generate(self, size):
        width, height = size

        layout_left = width * np.random.uniform(self.margin[0], self.margin[1])
        layout_top = height * np.random.uniform(self.margin[0], self.margin[1])
        layout_width = max(width - layout_left * 2, 0)
        layout_height = max(height - layout_top * 2, 0)
        layout_bbox = [layout_left, layout_top, layout_width, layout_height]

        text_layers, text_in_imgs, text_in_outputs = [], [], []
        layouts = self.layout.generate(layout_bbox)
        #self.reader.move(np.random.randint(len(self.reader)))
        while True:
            self.reader.move_to_line_by_random_position()
            for layout in layouts:
                font = self.font.sample()

                for bbox, align in layout:
                    x, y, w, h = bbox
                    text_layer, text_in_img, text_in_output = self.textbox.generate((w, h), self.reader, font)
                    # add parsing code for jsonl
                    self.reader.prev()

                    if text_layer is None:
                        continue

                    text_layer.center = (x + w / 2, y + h / 2)
                    if align == "left":
                        text_layer.left = x
                    if align == "right":
                        text_layer.right = x + w

                    self.textbox_color.apply([text_layer])
                    text_layers.append(text_layer)
                    text_in_imgs.append(text_in_img)
                    text_in_outputs.append(text_in_output)
            if len(text_layers) > 0:
                break

        self.content_color.apply(text_layers)

        return text_layers, text_in_imgs, text_in_outputs
