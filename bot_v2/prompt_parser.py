import re
import dalle_img_gen as dalle


class Parser:
    def __init__(self, response_text):
        self._response_text = response_text
        self._parsed_text = []
        self._parse_prompt()
        try:
            self._process_images()
        except Exception as e:
            self._delete_images()

    def _parse_prompt(self):
        pattern = r'(.*?)\[Image\]\{(.*?)\}'
        matches = re.findall(pattern, self._response_text)
        it = 0
        for match in matches:
            text, image_prompt = match

            if text.strip():
                parsed_text_input = {'text': text.strip()}
                self._parsed_text.append(parsed_text_input)
            parsed_image_prompt = {'image': image_prompt.strip()}
            self._parsed_text.append(parsed_image_prompt)

            it = self._response_text.find(pattern, it) + len(image_prompt) + len('[Image]{}')
        remaining_text = self._response_text[it:].strip()
        if remaining_text:
            parsed_text_input = {'text': remaining_text.strip()}
            self._parsed_text.append(parsed_text_input)

    def _process_images(self):
        for i in range(len(self._parsed_text)):
            if 'image' in self._parsed_text[i]:
                img_link = dalle.generate_img_link(self._parsed_text[i]['image'])
                self._parsed_text[i]['image'] = img_link

    def _delete_images(self):
        parsed_text_only = []
        for i in range(len(self._parsed_text)):
            if 'text' in self._parsed_text[i]:
                parsed_text_only.append(self._parsed_text[i])
        self._parsed_text = parsed_text_only

    def get_parsed_text(self):
        return self._parsed_text


if __name__ == "__main__":
    prompt = ("This is a simple prompt "
              "[Image]{A little gray crow }... "
              "More fillers we need more fillers [Image]{a dessert, and a camel crosses a horison} "
              "Ending, fwuh we did it. ")
    phrase = Parser(prompt)
    for paragraph in phrase.get_parsed_text():
        print(paragraph)
