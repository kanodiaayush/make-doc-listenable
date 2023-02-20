#!/usr/bin/env python3

import os
import textract
from PyPDF2 import PdfReader, PdfWriter

import openai,os,sys


# read in the pdf file
def clean_pdf(configs):
    pdf_file = configs['input_file']
    tmpdir = configs['tmpdir']
    start_page = configs['start_page']
    if start_page == -1:
        start_page = 0
    end_page = configs['end_page']
    if tmpdir == '':
        tmpdir = pdf_file.split('.')[0] + '_tmp'

    # split into pages, save
    if not os.path.exists(tmpdir):
        os.mkdir(tmpdir)

        # get the number of pages
    pdf = PdfReader(open(pdf_file, 'rb'))
    num_pages = len(pdf.pages)
    assert end_page <= num_pages, 'end_page is greater than the number of pages in the pdf'
    if end_page == -1:
        end_page = num_pages

    def pdf_to_text():
    # write each page to tmpdir
        for i in range(start_page, end_page):
            pdf_writer = PdfWriter()
            pdf_writer.add_page(pdf.pages[i])
            output_filename = '{}/page_{}.pdf'.format(tmpdir, i)
            # page_text = textract.process('{}/page_{}.pdf'.format(tmpdir, ii))
            with open(output_filename, 'wb') as out:
                pdf_writer.write(out)
            page_text = textract.process(output_filename)
            output_filename_txt = '{}/page_{}.txt'.format(tmpdir, i)
            with open(output_filename_txt, 'wb') as out:
                out.write(page_text)
            # remove pdf page
            os.remove(output_filename)

    def text_to_cleaned():
        # now extract only the text from the first page using textract
        pre_prompt = configs['pre_prompt']
        for ii in range(start_page, end_page):
            print("Cleaning page {}".format(ii))
            output_filename_txt = '{}/page_{}.txt'.format(tmpdir, ii)
            text = textract.process(output_filename_txt).decode('utf-8')
            prompt = f'{pre_prompt}\nSTART\n{text}'

            completions = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                temperature=0.05,
                max_tokens=2000,
            )
            message = completions['choices'][0]['text']

            # if 'pre_prompt_2' in configs:
            #     pre_prompt_2 = configs['pre_prompt_2']
            #     prompt = f'{pre_prompt_2}\nSTART\n{message}'

            #     completions = openai.Completion.create(
            #         model="text-davinci-003",
            #         prompt=prompt,
            #         temperature=0.05,
            #         max_tokens=2000,
            #     )
            #     message = completions['choices'][0]['text']

            output_filename = '{}/page_{}_cleaned{}.txt'.format(tmpdir, ii, configs['suffix'])
            #print(prompt)
            #print(message)
            #print("\n\n\n\n\n\n")
            with open(output_filename, 'w') as out:
                out.write(message)

    def cleaned_to_merged():
        # now merge all the pages into one file
        with open(f"{configs['output_file']}", 'w') as out:
            for ii in range(start_page, end_page):
                output_filename = '{}/page_{}_cleaned{}.txt'.format(tmpdir, ii, configs['suffix'])
                with open(output_filename, 'r') as f:
                    out.write(f.read())
                if configs['print_page_breaks']:
                    out.write(f'\n\n\n\n\n\n\n PAGE {ii} ENDS\n\n\n\n\n\n\n')
        if configs['output_to_pdf']:
            # write the contents of configs['output_file'] to configs['output_file'].pdf in pdf format
            # use pandoc
            pdf_output_file = configs['output_file'].split('.')[0] + '.pdf'
            os.system(f'pandoc {configs["output_file"]} -o {pdf_output_file} --pdf-engine=xelatex')

    def raw_to_merged():
        # now merge all the pages into one file
        with open(configs['output_file_raw'], 'w') as out:
            for ii in range(start_page, end_page):
                output_filename = '{}/page_{}.txt'.format(tmpdir, ii)
                with open(output_filename, 'r') as f:
                    out.write(f.read())
                out.write(f'\n\n\n\n\n\n\n PAGE {ii} ENDS\n\n\n\n\n\n\n')

    pdf_to_text()
    raw_to_merged()
    text_to_cleaned()
    cleaned_to_merged()

if __name__ == '__main__':
    from run_config import configs

    # Validate OPENAI_API_KEY
    if 'OPENAI_API_KEY' not in os.environ:
        print('OPENAI_API_KEY not found in environment variables')
        print('Please set the OPENAI_API_KEY environment variable')
        print('Aborting...')
        sys.exit(1)
    else:
        try:
            openai.Engine.list()
            print('OPENAI_API_KEY is valid')
        except:
            print('OPENAI_API_KEY is invalid')
            print('Please check the OPENAI_API_KEY environment variable')
            print('Aborting...')
            sys.exit(1)
    
    print('Enter input file path:')
    configs['input_file'] = input()

    configs['output_file'] = f"{configs['input_file'].split('.')[0]}_cleaned{configs['suffix']}.txt"

    print(f'Enter output file path (Press enter to default to {configs["output_file"]}):')
    configs['output_file'] = input()
    if configs['output_file'] == '':
        configs['output_file'] = f"{configs['input_file'].split('.')[0]}_cleaned{configs['suffix']}.txt"

    configs['output_file_raw'] = f"{configs['input_file'].split('.')[0]}_raw.txt"
    if configs['output_file'] == '':
        configs['output_file_raw'] = f"{configs['input_file'].split('.')[0]}_raw.txt"

    configs['tmpdir'] = f"{configs['input_file'].split('.')[0]}_tmp"

    print('Enter start page (Press enter to default to 0):')
    configs['start_page'] = input()
    if configs['start_page'] == '':
        configs['start_page'] = 0
    else:
        configs['start_page'] = int(configs['start_page'])
    print('Enter end page (Press enter to default to -1):')
    configs['end_page'] = input()
    if configs['end_page'] == '':
        configs['end_page'] = -1
    else:
        configs['end_page'] = int(configs['end_page'])

    print('Enter tmpdir (Press enter to default to {}):'.format(configs['tmpdir']))
    configs['tmpdir'] = input()
    if configs['tmpdir'] == '':
        configs['tmpdir'] = f"{configs['input_file'].split('.')[0]}_tmp"

    print('Enter if you want output to pdf (Press enter to default to False): (True/False)')
    print('Make sure pandoc is installed if you want to output to pdf')
    configs['output_to_pdf'] = input()
    if configs['output_to_pdf'] == '':
        configs['output_to_pdf'] = False
    else:
        if configs['output_to_pdf'] == 'True':
            configs['output_to_pdf'] = True
        else:
            configs['output_to_pdf'] = False

    print('Running:')
    clean_pdf(configs)
