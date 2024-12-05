from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from crud_functions import get_all_products, initiate_db

API_TOKEN = ''  # Укажите ваш токен API
initiate_db()
products_info = get_all_products()

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class UserState(StatesGroup):
    waiting_for_weight = State()
    waiting_for_growth = State()
    waiting_for_age = State()

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
button_calculate = KeyboardButton('Рассчитать')
button_info = KeyboardButton('Информация')
button_buy = KeyboardButton('Купить')
keyboard.add(button_calculate, button_info, button_buy)

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer('Привет! Я бот, помогающий твоему здоровью.\nВыберите действие:', reply_markup=keyboard)

@dp.message_handler(lambda message: message.text.lower() == 'рассчитать')
async def process_calculation(message: types.Message):
    await UserState.waiting_for_weight.set()
    await message.answer("Введите ваш вес (в кг):")

@dp.message_handler(state=UserState.waiting_for_weight)
async def process_weight(message: types.Message, state: FSMContext):
    try:
        weight = float(message.text)
        await state.update_data(weight=weight)
        await UserState.waiting_for_growth.set()
        await message.answer("Введите ваш рост (в см):")
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число для веса.")

@dp.message_handler(state=UserState.waiting_for_growth)
async def process_growth(message: types.Message, state: FSMContext):
    try:
        growth = float(message.text)
        await state.update_data(growth=growth)
        await UserState.waiting_for_age.set()
        await message.answer("Введите ваш возраст (в годах):")
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число для роста.")

@dp.message_handler(state=UserState.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    try:
        age = int(message.text)
        user_data = await state.get_data()
        weight = user_data['weight']
        growth = user_data['growth']
        calories = 10 * weight + 6.25 * growth - 5 * age + 5
        await message.answer(f"Ваши суточные калории: {calories:.2f} ккал.")
        await state.finish()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число для возраста.")

@dp.message_handler(commands=['buying_list'])
async def get_buying_list(message: types.Message):
    products_info = get_all_products()  # Получаем все продукты из базы данных
    await message.answer("Вот наши продукты:")
    for product in products_info:
        product_id, title, description, price = product
        photo_path = f'C:\\pythonlesson\\lesson14.1\\files\\{product_id}.jpg'  # Убедитесь, что путь к фотографии правильный
        try:
            with open(photo_path, 'rb') as photo:
                await message.answer_photo(photo=photo,
                                            caption=f'Название: {title} | Описание: {description} | Цена: {price} руб.')
        except FileNotFoundError:
            await message.answer(f'Фото для {title} не найдено.')

@dp.callback_query_handler(lambda call: call.data in [product[0] for product in products_info])
async def send_confirm_message(call: types.CallbackQuery):
    await call.message.answer("Вы выбрали продукт!")
    await bot.answer_callback_query(call.id)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)