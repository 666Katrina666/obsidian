import re
import os

# Функция для вставки двойного переноса между абзацами
def fix_paragraphs_line(line):
    # Вставляем абзацы после знака препинания + заглавная/тире
    pattern1 = r'([.!?…»])([A-ZА-ЯЁ—a-zа-яё«"])'
    line = re.sub(pattern1, r'\1\n\n\2', line)
    # Вставляем абзац между маленькой буквой и заглавной, если они подряд
    pattern2 = r'([a-zа-яё])([A-ZА-ЯЁ])'
    line = re.sub(pattern2, r'\1\n\n\2', line)
    return line

def process_file(input_path):
    # Новый путь с суффиксом ' fixed' перед расширением
    base, ext = os.path.splitext(input_path)
    output_path = base + ' fixed' + ext
    with open(input_path, encoding='utf-8') as infile, open(output_path, "w", encoding="utf-8") as outfile:
        for lineno, line in enumerate(infile):
            if lineno < 7:
                outfile.write(line)
            else:
                if line.strip():
                    fixed_line = fix_paragraphs_line(line.rstrip())
                    outfile.write(fixed_line + '\n')
                else:
                    outfile.write('\n')
    print(f'Done! Fixed text saved to {output_path}')

if __name__ == "__main__":
    import sys
    def process_range(start_num, end_num, directory="Fanfics"):
        for n in range(start_num, end_num + 1):
            input_path = os.path.join(directory, f"{n}.md")
            if not os.path.exists(input_path):
                print(f"Skip: file not found {input_path}")
                continue
            process_file(input_path)

    def print_usage():
        print("Usage:")
        print("  python fix_paragraphs.py path_to_file.md")
        print("  python fix_paragraphs.py START-END        # e.g., 324-333 (uses Fanfics/START..END.md)")
        print("  python fix_paragraphs.py START END        # e.g., 324 333 (uses Fanfics/START..END.md)")
        print("  python fix_paragraphs.py N                # e.g., 324 (uses Fanfics/324.md)")

    if len(sys.argv) < 2:
        print_usage()
    else:
        arg1 = sys.argv[1]
        # Case: range provided as START-END
        if len(sys.argv) == 2 and '-' in arg1:
            try:
                start_str, end_str = arg1.split('-', 1)
                start_num = int(start_str)
                end_num = int(end_str)
                if start_num > end_num:
                    start_num, end_num = end_num, start_num
                process_range(start_num, end_num)
            except ValueError:
                print_usage()
        # Case: two numbers START END
        elif len(sys.argv) == 3:
            try:
                start_num = int(sys.argv[1])
                end_num = int(sys.argv[2])
                if start_num > end_num:
                    start_num, end_num = end_num, start_num
                process_range(start_num, end_num)
            except ValueError:
                print_usage()
        # Case: single number N -> Fanfics/N.md
        else:
            try:
                n = int(arg1)
                process_file(os.path.join("Fanfics", f"{n}.md"))
            except ValueError:
                # Fallback: treat as a direct path
                process_file(arg1)
