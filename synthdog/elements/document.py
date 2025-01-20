"""
Donut
Copyright (c) 2022-present NAVER Corp.
MIT License
"""
import numpy as np
from synthtiger import components

from elements.content import Content
from elements.paper import Paper


class Document:
    def __init__(self, config):
        self.fullscreen = config.get("fullscreen", 0.5)
        self.landscape = config.get("landscape", 0.5)
        self.short_size = config.get("short_size", [480, 1024])
        self.aspect_ratio = config.get("aspect_ratio", [1, 2])
        self.paper = Paper(config.get("paper", {}))
        self.content = Content(config.get("content", {}))
        self.effect = components.Iterator(
            [
                components.Switch(components.ElasticDistortion()),
                components.Switch(components.AdditiveGaussianNoise()),
                components.Switch(
                    components.Selector(
                        [
                            components.Perspective(),
                            components.Perspective(),
                            components.Perspective(),
                            components.Perspective(),
                            components.Perspective(),
                            components.Perspective(),
                            components.Perspective(),
                            components.Perspective(),
                        ]
                    )
                ),
            ],
            **config.get("effect", {}),
        )

    def generate(self, size):
        width, height = size
        fullscreen = np.random.rand() < self.fullscreen

        if not fullscreen:
            landscape = np.random.rand() < self.landscape
            max_size = width if landscape else height
            # 根据输入图片尺寸动态计算最小宽度
            min_width_ratio = 0.7  # 最小宽度与图片短边的比例
            dynamic_min_width = int(min(width, height) * min_width_ratio)

            # 随机生成短边长度
            short_size = np.random.randint(
                min(width, height, self.short_size[0]),
                min(width, height, self.short_size[1]) + 1,
            )

            # 动态限制宽度的宽高比范围
            aspect_ratio = np.random.uniform(
                max(min(max_size / short_size, self.aspect_ratio[0]), dynamic_min_width / short_size),
                min(max_size / short_size, self.aspect_ratio[1]),
            )

            # 计算长边长度
            long_size = int(short_size * aspect_ratio)

            # 动态调整宽度（确保宽度大于动态计算的最小值）
            if landscape:  # 横向图片，宽度为长边
                if long_size < dynamic_min_width:
                    long_size = dynamic_min_width
            elif short_size < dynamic_min_width:  # 纵向图片，宽度为短边
                short_size = dynamic_min_width

            # 确定最终尺寸
            size = (long_size, short_size) if landscape else (short_size, long_size)

        text_layers, text_in_imgs, text_in_outputs = self.content.generate(size)
        paper_layer = self.paper.generate(size)
        self.effect.apply([*text_layers, paper_layer])

        return paper_layer, text_layers, text_in_imgs, text_in_outputs
