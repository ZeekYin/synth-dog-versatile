"""
Donut
Copyright (c) 2022-present NAVER Corp.
MIT License
"""
import numpy as np
from synthtiger import layers
import json


class TextBox:
    def __init__(self, config):
        self.fill = config.get("fill", [1, 1])

    def generate(self, size, text, font):
        width, height = size

        char_layers, chars = [], []
        fill = np.random.uniform(self.fill[0], self.fill[1])
        width = np.clip(width * fill, height, width)
        font = {**font, "size": int(height)}
        left, top = 0, 0

        read_full_line = False
        #read whole line in jsonl
        #take out the Q part.
        tmp_chars = []
        for char in text:
            # stop when encounter \r\n
            if char in "\r\n":
                read_full_line = True
                break
            tmp_chars.append(char)
        jsonl_text = "".join(tmp_chars).strip()
        #parse jsonl
        record = json.loads(jsonl_text)
        # record has: text_in_img, text_in_output,text1, text2, ...
        text_in_img = record.get("text_in_img")
        text_in_output = record.get("text_in_output")

        text = text_in_img


        for char in text:
            # stop when encounter \r\n
            if char in "\r\n":
                read_full_line = True
                break

            char_layer = layers.TextLayer(char, **font)
            char_scale = height / char_layer.height
            char_layer.bbox = [left, top, *(char_layer.size * char_scale)]
            if char_layer.right > width:
                break

            char_layers.append(char_layer)
            chars.append(char)
            left = char_layer.right

        text = "".join(chars).strip()
        
        if len(char_layers) == 0 or len(text) == 0 or not read_full_line:
            return None, None, None

        text_layer = layers.Group(char_layers).merge()

        return text_layer, text_in_img, text_in_output
