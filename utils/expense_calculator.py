class Calculator:

    @staticmethod
    def multiply(a:int, b:int) -> int:
        """
        Multiply two integers.

        Args:
            a (int): the first integer.
            b (int): the second integer.

        Returns:
            int: The product of a and b 
        """

        return a * b
    
    @staticmethod
    def calculate_total(*x:float) -> float:
        """
        calculate sun of the given list of numbers

        Args:
            x (list): list of floating numbers
        Returns:
            float: the sum of numbers in the list
        """

        return sum(x)
    
    @staticmethod
    def calculate_daily_budget(total:float, days: int) -> float:
        """
        Calculate daily budget
        Args:
            total (float): total Cost.
            days (int): total number of days
        Returns:
            float: Expense for a single day
        """

        return total / days if days > 0 else 0