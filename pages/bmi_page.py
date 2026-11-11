import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BmiCalculatorPage:
    URL = "https://www.calculator.net/bmi-calculator.html"
    AGE = (By.ID, "cage")
    HEIGHT_CM = (By.ID, "cheightmeter")
    WEIGHT_KG = (By.ID, "ckg")
    HEIGHT_FEET = (By.ID, "cheightfeet")
    HEIGHT_INCH = (By.ID, "cheightinch")
    WEIGHT_LB = (By.ID, "cpound")
    CALCULATE = (By.CSS_SELECTOR, 'input[type="submit"][value="Calculate"]')
    # На calculator.net очистка формы реализована кнопкой Clear.
    CLEAR = (By.CSS_SELECTOR, 'input[value="Clear"],button[value="Clear"],input[type="reset"]')
    CONTENT = (By.ID, "content")

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    def open(self):
        self.driver.get(self.URL)
        self.wait.until(EC.visibility_of_element_located(self.AGE))
        return self

    def metric(self):
        # Сайт принимает ctype=metric, поэтому не зависим от разметки вкладок.
        self.driver.get(self.URL + "?ctype=metric")
        self.wait.until(EC.visibility_of_element_located(self.HEIGHT_CM))
        return self

    def us(self):
        self.driver.get(self.URL + "?ctype=standard")
        self.wait.until(EC.visibility_of_element_located(self.HEIGHT_FEET))
        return self

    def _fill(self, locator, value):
        field = self.wait.until(EC.visibility_of_element_located(locator))
        field.clear()
        if value is not None:
            field.send_keys(str(value))
        return self

    def enter_metric(self, height_cm, weight_kg):
        self._fill(self.HEIGHT_CM, height_cm)
        self._fill(self.WEIGHT_KG, weight_kg)
        return self

    def enter_us(self, feet, inches, pounds):
        self._fill(self.HEIGHT_FEET, feet)
        self._fill(self.HEIGHT_INCH, inches)
        self._fill(self.WEIGHT_LB, pounds)
        return self

    def set_age(self, age):
        return self._fill(self.AGE, age)

    def field_value(self, locator):
        return self.wait.until(EC.presence_of_element_located(locator)).get_attribute("value")

    def metric_values(self):
        return (self.field_value(self.HEIGHT_CM),
                self.field_value(self.WEIGHT_KG))

    def calculate(self):
        old_url = self.driver.current_url
        self.wait.until(EC.element_to_be_clickable(self.CALCULATE)).click()
        # При HTML-валидации неверное поле может не дать отправить форму.
        # Не ждём смены URL безусловно: тогда неверный ввод вызывает timeout.
        self.wait.until(lambda d: d.current_url != old_url or
                        d.execute_script("return !!document.querySelector('input:invalid')"))
        return self

    def clear(self):
        self.wait.until(EC.element_to_be_clickable(self.CLEAR)).click()
        return self

    def result_text(self):
        content = self.wait.until(EC.visibility_of_element_located(self.CONTENT)).text
        return content

    def bmi_result(self):
        # Результат ищем в начале блока результатов, а не в справочном тексте ниже.
        text = self.result_text()
        match = re.search(r'BMI\s*=\s*([0-9]+(?:[.,][0-9]+)?)\s*kg/m', text, flags=re.I)
        if not match:
            raise AssertionError("Результат BMI не найден на странице")
        return float(match.group(1).replace(',', '.'))

    def bmi_category(self):
        text = self.result_text()
        match = re.search(r'BMI\s*=\s*[0-9]+(?:[.,][0-9]+)?\s*kg/m[^\n]*?\(([^)]+)\)', text, flags=re.I)
        if not match:
            raise AssertionError("Категория BMI не найдена на странице")
        return match.group(1).strip()

    def has_bmi_result(self):
        # Ищем только до раздела пояснений, а не формулу в статье ниже.
        text = self.result_text().split('BMI introduction', 1)[0]
        return bool(re.search(r'BMI\s*=\s*[0-9]+(?:[.,][0-9]+)?\s*kg/m', text))

    def has_invalid_field(self):
        return bool(self.driver.execute_script(
            "return document.querySelector('input:invalid') !== null"))
