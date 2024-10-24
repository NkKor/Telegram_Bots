import re


class Parser:
    def __init__(self, response_text):
        self._response_text = response_text
        self._parsed_text = []
        self._parse_prompt()

    def _parse_prompt(self):
        pattern = r"(.*?)\[IMAGE\]\{(.*?)\}"
        matches = re.findall(pattern, self._response_text)
        it = 0
        for match in matches:
            text,image_prompt = match
            if text.strip():
                parsed_text_input = {'text': text.strip()}
                self._parsed_text.append(parsed_text_input)
            parsed_image_prompt = {'IMAGE': image_prompt.strip()}
            self._parsed_text.append(parsed_image_prompt)

            it = self._response_text.find(pattern, it) + len(image_prompt) + len('[IMAGE]{}')
        remaining_text = self._response_text[it:].strip()
        if remaining_text:
            parsed_text_input = {'text':remaining_text.strip()}
            self._parsed_text.append(parsed_text_input)

    def get_parsed_text(self):
        return self._parsed_text

if __name__ == "__main__":
    prompt = ("This is a simple prompt "
              "[IMAGE]{A little gray crow}"
              "More fillers we need more fillers [IMAGE]{a dessert, and a camel crosses a horison}"
              "Ending, fwuh we did it.")
    phrase = Parser(prompt)
    for paragraph in phrase.get_parsed_text():
        print(paragraph)


