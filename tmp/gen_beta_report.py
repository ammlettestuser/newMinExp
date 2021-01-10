from mdutils import MdUtils
import sys
import csv

def gen_content():
    print("Generating content")
    mdFile = MdUtils(file_name="report", title="Experiment Report")
    mdFile.new_paragraph("The experiment generated the following results:")
    mdFile.new_paragraph("The classification rate after training on 5000 training examples is:")
    with open("../result.csv") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        for row in csv_reader:
            mdFile.new_paragraph(", ".join(row))
    return mdFile
    mdFile.new_paragraph("End Report.")

def save_content(file):
    print("Saving MD file")
    file.create_md_file()

def main(argvs):
    print("path is", argvs)
    file = gen_content()
    save_content(file)

if __name__ == "__main__":
    main(sys.argv[1:])
