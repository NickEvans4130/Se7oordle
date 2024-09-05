def remove_words_with_apostrophes(input_file, output_file):
    try:
        # Open the input file for reading
        with open(input_file, 'r') as infile:
            # Read all lines and strip any surrounding whitespace/newlines
            words = infile.readlines()
            words = [word.strip() for word in words]

        # Filter out words containing apostrophes
        filtered_words = [word for word in words if "'" not in word]

        # Open the output file for writing
        with open(output_file, 'w') as outfile:
            # Write each word on a new line
            for word in filtered_words:
                outfile.write(word + '\n')

        print(f"Filtered words have been written to {output_file}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Specify the input and output file paths
input_file = 'word_list.txt'
output_file = 'cleaned_word_list.txt'

# Call the function
remove_words_with_apostrophes(input_file, output_file)
