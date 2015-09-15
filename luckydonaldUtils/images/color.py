# -*- coding: utf-8 -*-

__author__ = 'luckydonald'

from ..dependencies import import_or_install
import_or_install("PIL", "Pillow")
from PIL import Image


def most_frequent_color(image, colors=10):
	image2 = image.convert("P", palette=Image.ADAPTIVE, colors=colors)
	image3 = image2.convert(image.mode)
	del image2

	w, h = image3.size
	pixels = image3.getcolors(w * h)

	most_frequent_pixels = [pixels[0]]

	for count, color in pixels:
		length = len(most_frequent_pixels)
		for i in range(0, length):
			if color == most_frequent_pixels[i][1]:
				break
			if count > most_frequent_pixels[i][0]:
				most_frequent_pixels.insert(i, (count, color))
				break
			elif count < most_frequent_pixels[length-1]:
				most_frequent_pixels.append((count, color))
				break
	del image3
	return most_frequent_pixels[:colors]