from win32more.Microsoft.UI.Xaml import GridLength, GridUnitType
from win32more.Microsoft.UI.Xaml.Controls import (
    ColumnDefinition,
    RowDefinition,
)


def grid_length_auto():
    grid_length = GridLength()
    grid_length.GridUnitType = GridUnitType.Auto

    return grid_length


def grid_length_star(value: int = 1):
    grid_length = GridLength()
    grid_length.GridUnitType = GridUnitType.Star
    grid_length.Value = value

    return grid_length


def column_definition_star(value: int = 1):
    column_definition = ColumnDefinition()
    column_definition.Width = grid_length_star(value)

    return column_definition


def row_definition_auto():
    row_definition = RowDefinition()
    row_definition.Height = grid_length_auto()

    return row_definition


def row_definition_star(value: int = 1):
    row_definition = RowDefinition()
    row_definition.Height = grid_length_star(value)

    return row_definition


def is_based_on_recursive(cls, ancestor):
    for parent in cls.__bases__:
        if parent == ancestor:
            return True
        elif is_based_on_recursive(parent, ancestor):
            return True

    return False


def is_based_on(cls, ancestor):
    if cls == ancestor:
        return True
    else:
        return is_based_on_recursive(cls, ancestor)
