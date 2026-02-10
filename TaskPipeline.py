#TaskPipeline.py
import string
import os

class TaskPipeline:
    def __init__(self, pdf_manager, extractor, snipper):
        self.pdf_manager = pdf_manager
        self.extractor = extractor
        self.snipper = snipper

    # Changed 'file_prefix' to 'menu' so we can access folder_name AND file_prefix
    def run(self, pdf_path, menu):
        
        # 1. Create the output folder if it doesn't exist
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
            
            clean_q = q_name.replace(" ", "")

            for sub_index, crop_rect in enumerate(sub_task_crops):
                letter_label = alphabet[sub_index % 26]
                
                # 2. Create the filename
                filename = f"{menu.file_prefix}_{clean_q}_{letter_label}.png"
                
                # 3. Combine folder and filename safely
                full_output_path = os.path.join(output_folder, filename)
                
                self.snipper.crop_and_save(page, crop_rect, full_output_path)

        self.pdf_manager.close_pdf()
        print(f"Finished processing: {pdf_path}")
