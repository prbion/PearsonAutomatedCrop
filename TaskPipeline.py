# TaskPipeline.py
import string
import os
import re
import pymupdf

# Fallback roman numeral labels in case PDF text extraction misses them
_ROMAN_FALLBACK = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii']


class TaskPipeline:
    def __init__(self, pdf_manager, extractor, snipper, exporter):
        self.pdf_manager = pdf_manager
        self.extractor   = extractor
        self.snipper     = snipper
        self.exporter    = exporter    

    def sanitize_filename(self, name):
        invalid_chars = r'[/<>:"|?*\\]'
        return re.sub(invalid_chars, '_', name)

    def run(self, pdf_path, menu):
        output_folder = menu.folder_name
        os.makedirs(output_folder, exist_ok=True)
        print(f"Processing... Images will be saved in: {output_folder}/")

        self.pdf_manager.open_file(pdf_path)
        num_pages = self.pdf_manager.get_page_count()
        alphabet  = string.ascii_lowercase

        for i in range(num_pages):
            page           = self.pdf_manager.get_current_page(i)
            q_name         = self.extractor.find_current_question_name(page)
            coords         = self.extractor.find_mark_coordinates(page)
            sub_task_crops = self.extractor.calculate_crop_areas(coords, page)
            clean_q        = self.sanitize_filename(q_name.replace(" ", ""))

            has_any_letters = any(
                self.extractor.has_letter_subtasks(page, crop)
                for crop in sub_task_crops
            )

            # ------------------------------------------------------------------
            # Build a "full question" image that spans ALL sub-task crops.
            # ------------------------------------------------------------------
            full_q_filename = None
            if sub_task_crops:
                first_crop  = sub_task_crops[0]
                last_crop   = sub_task_crops[-1]
                full_q_rect = pymupdf.Rect(
                    first_crop.x0, first_crop.y0,
                    first_crop.x1, last_crop.y1,
                )
                full_q_filename    = f"{menu.file_prefix}_{clean_q}.png"
                full_q_output_path = os.path.join(output_folder, full_q_filename)
                self.snipper.crop_and_save(page, full_q_rect, full_q_output_path)

            if not has_any_letters:
                if sub_task_crops and full_q_filename:
                    self.exporter.add_row(
                        year=menu.year, subject=menu.subject, paper=menu.paper,
                        question_no=clean_q, part="", sub_part="",
                        part_image_filename=full_q_filename,
                        question_image_filename=full_q_filename, level=menu.level
                    )
            else:
                hierarchy = self.extractor.detect_hierarchy(page, sub_task_crops)
                #print(f"  Question {clean_q}: detected hierarchy = {hierarchy}") 

                if hierarchy == 'roman_first':
                    # --------------------------------------------------------
                    # Parent level = roman numeral (i, ii …)
                    # Child level  = letter (a, b …)
                    # Output pattern: {meta}_{Q}_i.a, {meta}_{Q}_i.b, {meta}_{Q}_ii.a …
                    #
                    # The roman label only appears at the START of its section.
                    # Subsequent crops (e.g. the (b) crop under (i)) won't contain
                    # the roman label at all, so we carry it forward with current_roman.
                    # --------------------------------------------------------
                    current_roman = None #

                    for sub_index, crop_rect in enumerate(sub_task_crops):
                        found_roman = self.extractor.find_roman_label_for_crop(page, crop_rect)
                        if found_roman:
                            current_roman = found_roman

                        # Only fall back to index if we have never seen a roman label yet
                        roman_label = current_roman or _ROMAN_FALLBACK[sub_index % len(_ROMAN_FALLBACK)]

                        letter_coords = self.extractor.find_letter_coordinates_for_crop(
                            page, crop_rect
                        )

                        if letter_coords:
                            letter_crops = self.extractor.calculate_letter_crop_areas(
                                letter_coords, crop_rect
                            )
                            for letter_text, letter_crop in letter_crops:
                                part_filename    = f"{menu.file_prefix}_{clean_q}_{roman_label}.{letter_text}.png"
                                full_output_path = os.path.join(output_folder, part_filename)
                                self.snipper.crop_and_save(page, letter_crop, full_output_path)

                                self.exporter.add_row(
                                    year=menu.year, subject=menu.subject, paper=menu.paper,
                                    level=menu.level,
                                    question_no=clean_q, part=roman_label, sub_part=letter_text,
                                    part_image_filename=part_filename,
                                    question_image_filename=full_q_filename or part_filename,
                                )
                        else:
                            # Roman part with no letter children
                            part_filename    = f"{menu.file_prefix}_{clean_q}_{roman_label}.png"
                            full_output_path = os.path.join(output_folder, part_filename)
                            self.snipper.crop_and_save(page, crop_rect, full_output_path)

                            self.exporter.add_row(
                                year=menu.year, subject=menu.subject, paper=menu.paper,
                                level=menu.level,
                                question_no=clean_q, part=roman_label, sub_part="",
                                part_image_filename=part_filename,
                                question_image_filename=full_q_filename or part_filename,
                            )

                else:
                    # --------------------------------------------------------
                    # Parent level = letter (a, b …)
                    # Child level  = roman numeral (i, ii …)
                    # Output pattern: {meta}_{Q}_a.i, {meta}_{Q}_a.ii, {meta}_{Q}_b …
                    #
                    # Same carry-forward logic: letter labels only appear at the
                    # start of their section, so track current_letter across crops.
                    # --------------------------------------------------------
                    current_letter = None

                    for sub_index, crop_rect in enumerate(sub_task_crops):
                        found_letter = self.extractor.find_letter_label_for_crop(page, crop_rect)
                        if found_letter:
                            current_letter = found_letter

                        letter_label = current_letter or alphabet[sub_index % 26]

                        roman_coords = self.extractor.find_roman_numeral_coordinates(
                            page, crop_rect
                        )

                        if roman_coords:
                            roman_crops = self.extractor.calculate_roman_crop_areas(
                                roman_coords, crop_rect, page
                            )
                            for roman_text, roman_crop in roman_crops:
                                part_filename    = f"{menu.file_prefix}_{clean_q}_{letter_label}.{roman_text}.png"
                                full_output_path = os.path.join(output_folder, part_filename)
                                self.snipper.crop_and_save(page, roman_crop, full_output_path)

                                self.exporter.add_row(
                                    year=menu.year, subject=menu.subject, paper=menu.paper,
                                    level=menu.level,
                                    question_no=clean_q, part=letter_label, sub_part=roman_text,
                                    part_image_filename=part_filename,
                                    question_image_filename=full_q_filename or part_filename,
                                )
                        else:
                            part_filename    = f"{menu.file_prefix}_{clean_q}_{letter_label}.png"
                            full_output_path = os.path.join(output_folder, part_filename)
                            self.snipper.crop_and_save(page, crop_rect, full_output_path)

                            self.exporter.add_row(
                                year=menu.year, subject=menu.subject, paper=menu.paper,
                                level=menu.level,
                                question_no=clean_q, part=letter_label, sub_part="",
                                part_image_filename=part_filename,
                                question_image_filename=full_q_filename or part_filename,
                            )

        self.pdf_manager.close_pdf()
        print(f"Finished processing: {pdf_path}")
