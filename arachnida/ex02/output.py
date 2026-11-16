
def print_section(title, attrs):
    print(f"----- {title} -----")
    for label, value, in attrs:
        print(f" {label:<16}: {value}")