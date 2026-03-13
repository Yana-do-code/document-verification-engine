import re


class FieldExtractor:

    def extract(self, ocr_results):

        text_blob = " ".join([x["text"] for x in ocr_results])

        name_match = re.search(r"Name[:\s]+([A-Za-z\s]+)", text_blob)

        dob_match = re.search(
            r"\d{2}/\d{2}/\d{4}",
            text_blob
        )

        aadhaar_match = re.search(
            r"\d{4}\s\d{4}\s\d{4}",
            text_blob
        )

        data = {
            "name": name_match.group(1) if name_match else None,
            "dob": dob_match.group() if dob_match else None,
            "aadhaar_number": aadhaar_match.group() if aadhaar_match else None,
        }

        return data