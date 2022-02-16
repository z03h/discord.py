"""
The MIT License (MIT)

Copyright (c) 2021-present Rapptz & jay3332

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

import sys
from itertools import groupby
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .item import Item

__all__ = (
    'ItemWeights',
)


class ItemWeights:
    __slots__ = (
        'weights',
        'max_width',
        'max_rows',
    )

    def __init__(self, children: List[Item], *, max_width: int = 5, max_rows: int = 5) -> None:
        self.weights: List[int] = [0] * max_rows
        self.max_width: int = max_width
        self.max_rows: int = max_rows

        key = lambda i: sys.maxsize if i.row is None else i.row
        children = sorted(children, key=key)
        for row, group in groupby(children, key=key):
            for item in group:
                self.add_item(item)

    def find_open_space(self, item: Item) -> int:
        for index, weight in enumerate(self.weights):
            if weight + item.width <= self.max_width:
                return index

        raise ValueError('could not find open space for item')

    def add_item(self, item: Item) -> None:
        if item.row is not None:
            total = self.weights[item.row] + item.width
            if total > self.max_width:
                raise ValueError(f'item would not fit at row {item.row} ({total} > {self.max_width} width)')

            self.weights[item.row] = total
            item._rendered_row = item.row
        else:
            index = self.find_open_space(item)
            self.weights[index] += item.width
            item._rendered_row = index

    def remove_item(self, item: Item) -> None:
        if item._rendered_row is not None:
            self.weights[item._rendered_row] -= item.width
            item._rendered_row = None

    def clear(self) -> None:
        self.weights = [0] * self.max_rows
