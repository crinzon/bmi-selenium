import pytest
from pages.bmi_page import BmiCalculatorPage


# Взрослые, возраст 25 лет: 5 наборов корректных данных.
@pytest.mark.parametrize('height,weight', [
    (180, 72), (170, 65), (160, 50), (190, 90), (175, 80)
])
def test_metric_calculation(driver, height, weight):
    page = BmiCalculatorPage(driver).open().metric()
    page.set_age(25).enter_metric(height, weight).calculate()
    expected = weight / (height / 100) ** 2
    assert abs(page.bmi_result() - expected) <= 0.051


# Границы категорий для взрослых, вдали от неоднозначности округления.
@pytest.mark.parametrize('weight,category', [
    (46, 'Mild thinness'),  # BMI 17.97 при росте 160 см
    (48, 'Normal'),         # BMI 18.75
    (65, 'Overweight'),     # BMI 25.39
    (78, 'Obese Class I'),  # BMI 30.47
])
def test_bmi_category(driver, weight, category):
    page = BmiCalculatorPage(driver).open().metric()
    page.set_age(25).enter_metric(160, weight).calculate()
    assert page.bmi_category() == category


# Неверные данные должны отклоняться, а не давать допустимый результат.
@pytest.mark.parametrize('height,weight', [
    (0, 70), (-170, 70), (170, 0), (170, -70),
    ('abc', 70), (170, 'abc'), ('', 70), (170, ''),
    (170, '9' * 100),
])
def test_invalid_metric_input(driver, height, weight):
    page = BmiCalculatorPage(driver).open().metric()
    page.set_age(25).enter_metric(height, weight)
    old_url = page.driver.current_url
    page.calculate()
    # HTML-валидация может блокировать отправку до смены URL.
    # Если форма ушла на сервер, там не должно быть корректного результата.
    if page.driver.current_url != old_url:
        assert not page.has_bmi_result(), 'Некорректный ввод дал результат BMI'
    else:
        assert page.has_invalid_field(), 'Неверные данные не заблокированы'


def test_us_units(driver):
    page = BmiCalculatorPage(driver).open().us()
    page.set_age(25).enter_us(5, 10, 160).calculate()
    expected = 703 * 160 / (5 * 12 + 10) ** 2
    assert abs(page.bmi_result() - expected) <= 0.1


def test_output_rounding(driver):
    page = BmiCalculatorPage(driver).open().metric()
    page.set_age(25).enter_metric(175, 70).calculate()
    bmi = page.bmi_result()
    assert abs(bmi - 22.9) < 0.001


def test_clear(driver):
    page = BmiCalculatorPage(driver).open().metric()
    page.enter_metric(175, 70).clear()
    # Clear может сбрасывать форму к значениям по умолчанию, не обязательно к пустым строкам.
    height, weight = page.metric_values()
    assert height != '175'
    assert weight != '70'


def test_maximum_age(driver):
    # На сайте указан допустимый возраст 2–120 лет.
    page = BmiCalculatorPage(driver).open().metric()
    page.set_age(120).enter_metric(170, 70).calculate()
    expected = 70 / (1.70 ** 2)
    assert abs(page.bmi_result() - expected) <= 0.051
