# def fibonacci_generator(n):
#     a, b = 0, 1
#     count = 0
#     print('Generating')
#     while count < n:
#         yield a
#         a, b = b, a + b
#         count += 1
#
# # 使用生成器
# for number in fibonacci_generator(5):
#     print(number)

client_id = "1234"
# rd = "5678"
filename = f"server_processed_{client_id}_{rd}.wav"

print(filename)
