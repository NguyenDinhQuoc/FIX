
__all__ = ['parse_fix_options']


def parse_fix_options(user_input):
    split_options = user_input.split(' -')   #split by spaces
    action = split_options[0].strip()       #first item is the action to take

    options = {}
    for field in split_options[1:]:
        _field = field.strip().split()
        key          = _field[0]
        if len(_field[1:]) == 1:
            val      = _field[1]
        elif len(_field[1:])==0:
            print0("Value for tag {} not provided".format(key))
            raise IndexError
        else:
            val      = _field[1:]
            print0("Error when parsing using input. Too many values for tag {}".format(key))
        options[key] = val

    return action, options
