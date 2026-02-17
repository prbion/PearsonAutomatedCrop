#TaskPipeline.py
import string
import os
import re 
import pymupdf

class TaskPipeline:
    def __init__(self, pdf_manager, extractor, snipper):
        self.pdf_manager = pdf_manager
        self.extractor = extractor
        self.snipper = snipper

    def sanitize_filename(self, name):
        """Remove or replace characters that are invalid in filenames"""
        # Replace invalid characters with underscore
        invalid_chars = r'[/<>:"|?*\\]'
        return re.sub(invalid_chars, '_', name)

    def run(self, pdf_path, menu):
        
        output_folder = menu.folder_name
        os.makedirs(output_folder, exist_ok=True)
        print(f"Processing... Images will be saved in: {output_folder}/")

        self.pdf_manager.open_file(pdf_path)
        num_pages = self.pdf_manager.get_page_count()
        alphabet = string.ascii_lowercase

        for i in range(num_pages):
            page = self.pdf_manager.get_current_page(i)
            
            q_name = self.extractor.find_current_question_name(page)
            coords = self.extractor.find_mark_coordinates(page)
            sub_task_crops = self.extractor.calculate_crop_areas(coords, page)
            
            # CHANGED: Sanitize the question name to remove invalid filename characters
            clean_q = self.sanitize_filename(q_name.replace(" ", ""))

            # Check if this question has any letter subtasks at all
            has_any_letters = any(
                self.extractor.has_letter_subtasks(page, crop) 
                for crop in sub_task_crops
            )

            if not has_any_letters:
                # No letter subtasks - save the whole question as one image
                if sub_task_crops:
                    # Combine all crops into one big crop from first to last
                    first_crop = sub_task_crops[0]
                    last_crop = sub_task_crops[-1]
                    full_crop = pymupdf.Rect(
                        first_crop.x0, 
                        first_crop.y0, 
                        first_crop.x1, 
                        last_crop.y1
                    )
                    
                    filename = f"{menu.file_prefix}_{clean_q}.png"
                    full_output_path = os.path.join(output_folder, filename)
                    self.snipper.crop_and_save(page, full_crop, full_output_path)
            else:
                # Has letter subtasks - process each one
                for sub_index, crop_rect in enumerate(sub_task_crops):
                    letter_label = alphabet[sub_index % 26]
                    
                    # Check if this subtask has roman numeral subdivisions
                    roman_coords = self.extractor.find_roman_numeral_coordinates(page, crop_rect)
                    
                    if roman_coords:
                        # Has sub-subtasks like (i), (ii), etc.
                        roman_crops = self.extractor.calculate_roman_crop_areas(roman_coords, crop_rect, page)
                        
                        for roman_text, roman_crop in roman_crops:
                            filename = f"{menu.file_prefix}_{clean_q}_{letter_label}.{roman_text}.png"
                            full_output_path = os.path.join(output_folder, filename)
                            self.snipper.crop_and_save(page, roman_crop, full_output_path)
                    else:
                        # No sub-subtasks, save normally with letter
                        filename = f"{menu.file_prefix}_{clean_q}_{letter_label}.png"
                        full_output_path = os.path.join(output_folder, filename)
                        self.snipper.crop_and_save(page, crop_rect, full_output_path)

        self.pdf_manager.close_pdf()
        print(f"Finished processing: {pdf_path}")
