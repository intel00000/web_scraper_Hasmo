import scrapy
import re
import os
import json
from urllib.parse import urljoin
from pathlib import Path

class MckinseyCaseStudiesSpider(scrapy.Spider):
    name = 'mckinsey_case_studies'
    start_urls = ['https://www.mckinsey.com/about-us/case-studies']

    def parse(self, response):
        # Extract the container with the relevant elements
        container = response.css('#skipToMain > div:nth-child(2)')
        
        # Select the elements with the necessary data
        elements = container.css('.mdc-u-grid')
        for element in elements:
            title = element.css('[data-component="mdc-c-heading"]::text').get()
            description = element.css('[data-component="mdc-c-description"]::text').get()
            picture_url = element.css('[data-component="mdc-c-icon"] img::attr(src)').get()
            link = element.css('a::attr(href)').get()
            
            if title and description and picture_url and link:
                # Build the full URL for the image and link
                picture_url = urljoin(response.url, picture_url)
                link = urljoin(response.url, link)
                
                # Clean up the title for use as a folder name
                folder_name = re.sub(r'[<>:"/\\|?*]', ' ', title)
                
                # Prepare the data dictionary
                data = {
                    'title': title,
                    'description': description,
                    'picture': picture_url,
                    'link': link,
                }
                
                # Yield the item to save the data and download the image
                yield scrapy.Request(url=picture_url, callback=self.save_data,
                                     meta={'folder_name': folder_name, 'data': data})
    
    def save_data(self, response):
        # Get the folder name and data from the meta
        folder_name = response.meta['folder_name']
        data = response.meta['data']
        
        # Create the necessary folders
        base_path = Path('mckinsey/case-studies')
        folder_path = base_path / folder_name
        
        if not folder_path.exists():
            folder_path.mkdir(parents=True, exist_ok=True)
        
        # Save the data as a JSON file
        with open(folder_path / 'data.json', 'w') as f:
            json.dump(data, f)
        
        # Save the image
        with open(folder_path / 'picture.jpg', 'wb') as f:
            f.write(response.body)