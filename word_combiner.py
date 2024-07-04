def read_file(file_path):
    """Read words from a file and return a set of unique words."""
    with open(file_path, 'r') as file:
        words = set(file.read().splitlines())
    return words

def write_file(words, file_path):
    """Write words to a file, one per line."""
    with open(file_path, 'w') as file:
        for word in sorted(words):
            file.write(f"{word}\n")

def combine_files(file1, file2, output_file):
    """Combine words from two files into a new file without duplicates."""
    words1 = read_file(file1)
    words2 = read_file(file2)
    combined_words = words1.union(words2)
    write_file(combined_words, output_file)

# Example usage:
file1 = 'word_list.txt'
file2 = 'word_list_2.txt'
output_file = 'combined.txt'
combine_files(file1, file2, output_file)
