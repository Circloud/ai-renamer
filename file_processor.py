import markitdown
from openai import OpenAI
import os

class FileProcessor:
    def __init__(self, settings, ai_service):
        self.settings = settings
        self.ai_service = ai_service
        self.markitdown_excluded_extensions = [".md"]
    

    def extract_content(self, file_path):
        """Extract the content of the file using MarkItDown"""

        # Get file extension
        file_extension = os.path.splitext(file_path)[1]

        # Special case for MarkItDown
        if file_extension in self.markitdown_excluded_extensions:
            if file_extension == ".md":
                with open(file_path, "r") as f:
                    file_content = f.read()
                print(f"\n\n\n-----------------\n\n\n# FileProcessor extract_content Special Case Response:\n\n{file_content}")
                return True, file_content
        
        # Extract content using MarkItDown
        else:
            # Get the LLM provider to use provider-specific settings
            llm_provider = self.settings.get('llm_provider')
            print(f"\n\n\n-----------------\n\n\n# FileProcessor extract_content LLM Provider:\n\n{llm_provider}")

            client = OpenAI(
                api_key=self.settings.get(f'{llm_provider}_api_key'),
                base_url=self.settings.get(f'{llm_provider}_api_base_url')
            )

            try:
                md = markitdown.MarkItDown(llm_client=client, llm_model=self.settings.get(f'{llm_provider}_model'))

                result = md.convert(file_path)
                print(f"\n\n\n-----------------\n\n\n# FileProcessor extract_content MarkItDown Response:\n\n{result.text_content}")
                return True, result.text_content
            
            # Handle unsupported format error from MarkItDown
            except markitdown.UnsupportedFormatException as e:
                print(f"\n\n\n-----------------\n\n\n# FileProcessor extract_content MarkItDown Error:\n\n{str(e)}")
                return False, f"Unsupported file format: {str(e)}"
            
            # Handle empty file error from MarkItDown
            except ValueError as e:
                if "Input was empty" in str(e):
                    print(f"\n\n\n-----------------\n\n\n# FileProcessor extract_content MarkItDown Error:\n\n{str(e)}")
                    return True, "Blank file"
                return False, f"Unsupported file format: {str(e)}"
                
            except Exception as e:
                print(f"\n\n\n-----------------\n\n\n# FileProcessor extract_content MarkItDown Error:\n\n{str(e)}")
                return False, f"Error extracting file content: {str(e)}"


    def process_file(self, file_path):
        """Process the file by calling AIService and rename the file"""
        # Get file content from extract_content
        success, file_content = self.extract_content(file_path)
        if not success:
            return False, file_content  # Return the error message if extraction failed
            
        file_extension = os.path.splitext(file_path)[1]

        # Get file name suggestion or error message from AIService
        success, suggestion = self.ai_service.get_suggestion(file_content, file_extension)
        
        if not success:
            return False, suggestion # Return the error message if AI service call failed

        # Rename the file
        try:
            # Get new file path
            directory = os.path.dirname(file_path)
            new_file_path = os.path.join(directory, suggestion)
            
            # Check if target file already exists
            if os.path.exists(new_file_path):
                base, ext = os.path.splitext(new_file_path)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                new_file_path = f"{base}_{counter}{ext}"
            
            # Rename the file
            os.rename(file_path, new_file_path)
            return True, f"Successfully rename to {os.path.basename(new_file_path)}"
        
        except OSError as e:
            return False, f"Failed to rename file: {str(e)}"