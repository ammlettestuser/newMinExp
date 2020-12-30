import Mdutils
import sys

def gen_content():
    print("Generating content")
    mdFile = Mdutils(file_name="report", title="Beta_Report")
    mdFile.new_paragraph("Why do phd students get holidays and we don't? :) ")
    mdFile.create_md_file()

def save_content(location):
    print("Saving MD file")

def main(argvs):
    content = gen_content()
    #save_content(argvs[0])

if __name__ == "__main__":
    main(sys.argv[1:])