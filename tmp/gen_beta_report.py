from mdutils import MdUtils
import sys

def gen_content():
    print("Generating content")
    mdFile = MdUtils(file_name="report", title="Beta_Report")
    mdFile.new_paragraph("Why do phd students get holidays and we don't?")
    return mdFile

def save_content(file):
    print("Saving MD file")
    file.create_md_file()

def main(argvs):
    print("path is", argvs)
    file = gen_content()
    save_content(file)

if __name__ == "__main__":
    main(sys.argv[1:])
