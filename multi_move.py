# TODO: figure out how to efficiently batch import from a different directory
from board import Board, Dice
from bgexceptions import BackgammonException, IllegalMoveException
# try to add some multitasking
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool


class BarMove(object):
    """ Methods for removing checkers from the Bar. """
    def __init__(self, player, die, board, end):
        self.player = player
        self.other_player = Board.get_opponent(player)
        self.die = die
        self.board = board.copy_board()
        
        # check if end is on the board
        if not Board.on_board(end):
            raise IllegalMoveException("End is not on the Board!")
        else:
            self.end = end

    def make_move(self):
        """ Validates the movement given the provided board situation. """
        if not (self.die == abs(Board.get_home(self.other_player) - self.end)):
            raise IllegalMoveException("Off-Bar not possible: \
                                Die cannot be used to perform this movement!")

        # check if bar is empty and raise error if yes
        if self.board.get_bar(self.player) == 0:
            raise IllegalMoveException("Off-Bar not possible: \
                                        No checkers on the Bar!")

        # check if end position is in the homeboard of the other player
        # if not raise Error, checkers leaving the bar must be placed in the
        # homeboard of the opponent (your starting quadrant)
        if not Board.in_home_board(self.other_player, self.end):
            raise IllegalMoveException("Off-Bar not possible: \
                            Checkers must go into the opponents home board!")

        # check if there is more than one opponent checker at end position
        # and raise error when yes 
        if self.board.get_checkers(self.end, self.other_player) > 1:
            raise IllegalMoveException("Off-Bar not possible: \
                                        Location occupied by other player")

        # now make the movement:
        # first kick enemy checkers onto the bar if there are any
        if self.board.get_checkers(self.end, self.other_player) == 1:
            self.board.remove_from_location(self.other_player, self.end)
            self.board.move_to_bar(self.other_player)

        self.board.remove_from_bar(self.player)
        self.board.move_to_location(self.player, self.end)

        return self.board

    def __str__(self):
        """ Returns string representation of this movement. """
        return "bar --> %s" %(self.end + 1)

    def __eq__(self, other):
        """ Returns whether this movement is equal to the provided object. """
        if isinstance(other, BarMovement):
            return other.end == self.end
        else:
            return False

    def __ne__(self, other):
        return not self == other


class BearOffMove(object):
    """ Methods for bearing off a checker. """
    # rules for bear-off:
    # - all checkers must be in the homeboard of a color (end area)
    # - endboard numbered 1...6 with 1 closest to end of gameboard
    #   and 6 closest to bar
    # - roll a 1, bear off checker from 1
    # - roll a 6, bear off checker from 6
    # - if no checker at rolled position in homeboard, make legal move
    #   within the homeboard
    # - when number is rolled that is higher than the highest point with checkers,
    #   bear off next highest checker
    
    def __init__(self, player, die, board, start):
        # calls the __init__ of the super class Movement with player 
        # as the argument, makes it an instance attribute
        # within this class too
        self.player = player
        self.die = die
        self.board = board.copy_board()
        
        if not Board.on_board(start):
            raise IllegalMoveException("Start is not on the board!")
        else:
            self.start = start

    def can_use(self):
        """ Returns whether or not this movement can use the given
            dice roll to perform its movement. """
        # # returns 1 for white, black -1
        # direction = Board.get_direction(self.player)
        
        # # end must be start of the own homeboard
        # # which is 18 for white, and 5 for black
        # end = Board.get_home(self.player) - (direction * 6)

        # # loop from start position of movement towards the own starting zone
        # # (the opponents homeboard), while staying in own homeboard
        # for i in range(self.start - direction, end - direction, -direction):
        #   if self.board.get_checkers(i, self.player) > 0:
        #       # check if roll matches homeboard position 1..6
        #       return 
        
        # if die roll is higher than highest checkers in homeboard,
        # the highest checker can be removed    
        if self.die == abs(self.start - Board.get_home(self.player)):
            return True
        elif self.die >= abs(self.start - Board.get_home(self.player)):
            return True
        else:
            return False

    def make_move(self):
        """ Validates this movement given the provided
            board situation. """
        if not self.can_use():
            raise IllegalMoveException("Bear-off not possible: \
                                        Cannot use dice for this movement!")
            
        if self.board.get_checkers(self.start, self.player) == 0:
            raise IllegalMoveException("Bear-off not possible: \
                                        No checkers at location!")

        if self.board.get_bar(self.player) > 0:
            raise IllegalMoveException("Bear-off not possible: \
                                    Checkers from the bar must be moved first!")

        # loop over whole board and check whether all checkers are in the homeboard
        # if not all checkers are in the homeboard, bear-off is NOT allowed
        for i in range(Board.NUM_POINTS):
            if (self.board.get_checkers(i, self.player) > 0) and \
                                    (not Board.in_home_board(self.player, i)):
                raise IllegalMoveException("Bear-off not possible: \
                                    Still checkers outside of the home board!")

        # now make the move
        self.board.remove_from_location(self.player, self.start)
        self.board.move_off(self.player)

        return self.board

    def __str__(self):
        """ Returns string representation of this movement. """
        return "%s --> off" %(self.start + 1)

    def __eq__(self, other):
        """ Returns whether this movement is equal to the provided object. """
        if isinstance(other, BearOffMovement):
            return other.start == self.start
        else:
            return False

    def __ne__(self, other):
        return not self == other


class NormalMove(object):
    """ Methods for a normal movement. """

    def __init__(self, player, die, board, start, end):
        self.player = player
        self.other_player = Board.get_opponent(player)
        self.die = die
        self.board = board.copy_board()

        if (not Board.on_board(start)) or (not Board.on_board(end)):
            raise IllegalMoveException("Start or end is not on the board!")
        else:
            self.start = start
            self.end = end

    def make_move(self):
        """ Validates this movement given the provided
            board situation. """
        if not (self.die == abs(self.start - self.end)):
            #print "make_move2"
            raise IllegalMoveException("Normal move not possible: \
                                            Cannot use die for this movement!")
            
        if self.start == self.end:
            raise IllegalMoveException("Normal move not possible: \
                                Start and end must not be the same position!")
            
        if abs(self.start - self.end) > Dice.MAX_VALUE:
            raise IllegalMoveException("Normal move not possible: \
                                        Move distance larger than 6!")
            
        if self.board.get_bar(self.player) > 0:
            raise IllegalMoveException("Normal move not possible:: \
                                    Checkers from the bar must be moved first!")

        if self.board.get_checkers(self.start, self.player) == 0:
            raise IllegalMoveException("Normal move not possible: \
                                        No checkers at the start location!")
            
        if ((self.start > self.end) and (Board.get_direction(self.player) > 0) or
            (self.start < self.end) and (Board.get_direction(self.player) < 0)):
            raise IllegalMoveException("Normal move not possible: \
                                        Backward movements are not allowed!")
            
        if self.board.get_checkers(self.end, self.other_player) > 1:
            raise IllegalMoveException("Normal move not possible: \
                        End location already occupied by opponent checkers!")
        
        if self.board.get_bar(self.player) > 0:
            raise IllegalMoveException("Normal move not possible: \
                                    Checkers from the bar must be moved first!")

        # now perform movement:
        # check first whether the move bumps the opponent
        if self.board.get_checkers(self.end, self.other_player) == 1:
            self.board.remove_from_location(self.other_player, self.end)
            self.board.move_to_bar(self.other_player)

        # now perform the move
        self.board.remove_from_location(self.player, self.start)
        self.board.move_to_location(self.player, self.end)
        
        return self.board

    def __str__(self):
        """ Returns a String representation of this movement. """
        return "%s --> %s" %(self.start + 1, self.end + 1)

    def __eq__(self, other):
        """ Returns whether this movement is equal to the provided object. """
        if isinstance(other, NormalMovement):
            return (other.start == self.start) and (other.end == self.end)
        else:
            return False

    def __ne__(self, other):
        return not self == other


class BoardFactory(object):
    """ Generates all distinct boards for the given gammon situation
        and the provided dice roll. """

    @classmethod
    def generate_all_boards(cls, player, dice, board):
        """ Function takes an initial backgammon situation (player, dice, board),
            and generates all possible moves and the resulting boards.
            Returns a list of all possible moves from all dice combinations. """
        #print "Player: ", player
        #print "Dice: ", dice
        # check if dice are doubles:
        if dice.is_doubles():
            all_dice_combinations = [[dice.get_die1()] * 4]
        else:
            all_dice_combinations = []
            # make all dice combinations by sorting and put them in the list
            all_dice_combinations.append(sorted(dice.get_dice(), reverse=True))
            all_dice_combinations.append(sorted(dice.get_dice(), reverse=False))

        # all_boards will contain all possible boards in the end
        all_boards = []

        # loop over the two dice combinations
        # if doubles, all_dice_combinations contains list of 4 numbers
        for all_dice in all_dice_combinations:
            # set boards to the starting board
            boards = [board]
            # loop over die in one dice combination
            for die in all_dice:
                # maybe we can speed up the generation of boards
                # lets's try some multithreading:
                # create parallel threads for multithreading
                pool = ThreadPool(6)
                # bring input args in a form map() can deal with
                input_args = [(player, die, board_item) for board_item in boards]
                #print input_args
                # do the job on parallel threads
                computed_boards = pool.map(cls.compute_boards_wrapper, input_args)
                # close the pool    
                pool.close()
                # wait for worker processes to exit
                #pool.join()
                
                # check if there were any boards created and set these as
                # the starting boards for the next moves using the next die
                if len(computed_boards) >= 1:
                    boards = [item for sublist in computed_boards for item in sublist]
                
            # store all generated boards in all_boards
            # now repeat this process for the next dice combination
            all_boards.append(boards)

        # flatten removes dimensions --> instead of list of lists of lists,
        # this will return a list with all possible moves (ie boards) 
        lst = [item for sublist in all_boards for item in sublist]
        # transform list to set to get rid of duplicate boards
        # boards entering a set get key depending on their hash value and
        # identical boards will have identical hashes and removed from the set
        result = set(lst)
        # now transfrom back into list, because sets are unordered and cant
        # be accessed by keys directly
        return list(result)

    @classmethod
    def compute_boards_wrapper(cls, args):
        """ Utility function for multithreading. This is essential since
            map() cannot deal with multiple arguments. """
        return cls.compute_boards(*args)

    @staticmethod
    def compute_boards(player, die, board):
        """ Function takes a starting board and replaces it with all possible
            boards. Finally returns a list of all possible boards,
            or the starting board(s) if no boards could be created. """
        
        new_boards = []
        # check if bar move must be made
        if board.get_bar(player) > 0:
            try:
                # make a bar move, and return the resulting board
                destination = Board.get_home(Board.get_opponent(player)) + \
                                        die * Board.get_direction(player)
                #print "bar dest: ", destination + 1
                bar_move = BarMove(player, die, board, destination)
                tmp_board = bar_move.make_move()
                #print "BarMove"
            except IllegalMoveException:
                tmp_board = None
            # make sure a bar move was legal and a new board was generated
            # if yes, append new_boards
            if tmp_board is not None:
                new_boards.append(tmp_board)
                return new_boards
        # try normal or bear-off moves:
        else:   
            # loop over whole board
            for pos in range(Board.NUM_POINTS):
                # pos occupied by player
                if board.get_checkers(pos, player) > 0:
                    try:
                        # try to make a normal move and return resulting board
                        destination = pos + (die * Board.get_direction(player))
                        normal_move = NormalMove(player, die, board, pos, destination)
                        tmp_board = normal_move.make_move()
                        #print "NormalMove"
                    except IllegalMoveException, e:
                        tmp_board = None
                    # make sure normal move was legal and a new board was generated
                    # if yes, append new_boards
                    if tmp_board is not None:
                        new_boards.append(tmp_board)
            # loop over players homeboard, ie the target quadrant
            # of a player (white: 23...18 or black: 0...5)
            for pos in range(Board.get_home(player) - Board.get_direction(player),\
                Board.get_home(player) - (7 * Board.get_direction(player)),\
                 - Board.get_direction(player)):
                    try:
                        # try to bear off checkers and return resulting board
                        bear_off_move = BearOffMove(player, die, board, pos)
                        tmp_board = bear_off_move.make_move()
                        #print "BearOffMove"
                    except IllegalMoveException, e:
                        tmp_board = None
                    # make sure bearoff move was legal and a new board was generated
                    # if yes, append new_boards
                    if tmp_board is not None:
                        new_boards.append(tmp_board)
        
        # check if new boards were created
        # and if yes, replace each starting board in boards with
        # a list of possible boards originating from each starting board
        if len(new_boards) > 0:
            #print new_boards
            return new_boards
        elif len(new_boards) == 0:
            #print "no new_boards", [board]
            return [board]





# def timed():
#     """Stupid test function"""
#     b = Board()
#     d = Dice()
#     d.roll()
#     BoardFactory.generate_all_boards(0, d, b)

# if __name__ == '__main__':
#     import timeit
    
#     time = timeit.timeit("timed()", setup="from __main__ import timed", number=10)

#     print "Mean:", time/10, "s"
