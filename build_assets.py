import os
import shutil

from django.conf import settings


def build():
    image_files = [
        os.path.join(
            settings.BASE_DIR,
            'themes',
            'bloomsbury',
            'assets',
            'preprint_thumb.jpg'
        ),
        os.path.join(
            settings.BASE_DIR,
            'themes',
            'bloomsbury',
            'assets',
            'ucl_press_footer.svg'
        ),
        os.path.join(
            settings.BASE_DIR,
            'themes',
            'bloomsbury',
            'assets',
            'js',
            'toc.js',
        )
    ]
    dest_path = os.path.join(
        settings.BASE_DIR,
        'static',
        'bloomsbury',
        'assets',
    )

    if not os.path.exists(dest_path):
        os.makedirs(dest_path)

    for image_file in image_files:
        print("Copying file for bloomsbury theme.")
        shutil.copy(
            image_file,
            dest_path
        )
