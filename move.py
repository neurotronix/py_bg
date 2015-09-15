# TODO: figure out how to efficiently batch import from a different directory
from board import Board, Dice
from bgexceptions import BackgammonException, IllegalMoveException
import numpy as np

class BarMove(object):
	""" Methods for moving from the Bar. """

	def __init__(self, player, die, board, end):
		# calls the __init__ of the super class Movement
		# with player as the argument, makes it an instance attribute
		# within this class too
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
			raise IllegalMoveException("Off-Bar not possible: Die cannot be used to perform this movement!")

		# check if bar is empty and raise error if yes
		if self.board.get_bar(self.player) == 0:
			raise IllegalMoveException("Off-Bar not possible: No checkers on the Bar!")

		# check if end position is in the homeboard of the other player
		# if not raise Error, checkers leaving the bar must be placed in the
		# homeboard of the opponent (your starting quadrant)
		if not Board.in_home_board(self.other_player, self.end):
			raise IllegalMoveException("Off-Bar not possible: Checkers must go into the opponents home board!")

		# check if there is more than one opponent checker at end position
		# and raise error when yes 
		if self.board.get_checkers(self.end, self.other_player) > 1:
			raise IllegalMoveException("Off-Bar not possible: Location occupied by other player")

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
	#	and 6 closest to bar
	# - roll a 1, bear off checker from 1
	# - roll a 6, bear off checker from 6
	# - if no checker at rolled position in homeboard, make legal move within the homeboard
	# - when number is rolled that is higher than the highest point with checkers,
	#	bear off next highest checker
	
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
		# 	if self.board.get_checkers(i, self.player) > 0:
		# 		# check if roll matches homeboard position 1..6
		# 		return 
		
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
			raise IllegalMoveException("Bear-off not possible: Cannot use dice for this movement!")
			
		if self.board.get_checkers(self.start, self.player) == 0:
			raise IllegalMoveException("Bear-off not possible: No checkers at location!")

		if self.board.get_bar(self.player) > 0:
			raise IllegalMoveException("Bear-off not possible: Checkers from the bar must be moved first!")

		# loop over whole board and check whether all checkers are in the homeboard
		# if not all checkers are in the homeboard, bear-off is NOT allowed
		for i in range(Board.NUM_POINTS):
			if (self.board.get_checkers(i, self.player) > 0) and (not Board.in_home_board(self.player, i)):
				raise IllegalMoveException("Bear-off not possible: Still checkers outside of the home board!")

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
			raise IllegalMoveException("Normal move not possible: Cannot use die for this movement!")
			
		if self.start == self.end:
			raise IllegalMoveException("Normal move not possible: Start and end must not be the same position!")
			
		if abs(self.start - self.end) > Dice.MAX_VALUE:
			raise IllegalMoveException("Normal move not possible: Move distance larger than 6!")
			
		if self.board.get_bar(self.player) > 0:
			raise IllegalMoveException("Normal move not possible:: Checkers from the bar must be moved first!")

		if self.board.get_checkers(self.start, self.player) == 0:
			raise IllegalMoveException("Normal move not possible: No checkers at the start location!")
			
		if ((self.start > self.end) and (Board.get_direction(self.player) > 0) or
			(self.start < self.end) and (Board.get_direction(self.player) < 0)):
			raise IllegalMoveException("Normal move not possible: Backward movements are not allowed!")
			
		if self.board.get_checkers(self.end, self.other_player) > 1:
			raise IllegalMoveException("Normal move not possible: End location already occupied by opponent checkers!")
			
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

	### New approach with Raphael:
	@classmethod
	def generate_all_boards(cls, player, dice, board):
		# check if dice are doubles:
		if dice.is_doubles():
			all_dice_combinations = [[dice.get_die1()] * 4]
		else:
			all_dice_combinations = []
			# make all dice combinations by sorting and put them in the list
			all_dice_combinations.append(sorted(dice.get_dice(), reverse=False))
			all_dice_combinations.append(sorted(dice.get_dice(), reverse=True))

		# all_boards will contain all possible boards in the end
		all_boards = []

		# loop over the two dice combinations when not doubles
		# when doubles all_dice_combinations contains list of 4 numbers
		for all_dice in all_dice_combinations:
			# set boards to the starting board
			boards = [board]
			# loop over die in a dice combination
			for die in all_dice:
				bar = False
				# check if player must empty bar first
				if boards[0].get_bar(player) > 0:
					# this will return only one board if a bar move is possible
					tmp_board = cls.compute_boards(player, die, boards, bar=True)
					# check if bar move was made
					if tmp_board is not None:
						bar = True
					# if bar move was possible and legal add to boards
					if bar:
						boards = tmp_board
				# else if bar is empty
				# try normal or bearoff moves
				else:
					# returns all possible normal or bear-off boards
					boards = cls.compute_boards(player, die, boards)

			all_boards.append(boards)

		# flatten removes dimensions --> instead of list of lists of lists,
		# this will return a list with all possible moves (ie boards) 
		lst = [item for sublist in all_boards for item in sublist]
		print "lst:", lst
		result = set(lst)
		return list(result)

	# takes a starting board and replaces it with all possible boards
	# returns a list of a list of possible boards
	@staticmethod
	def compute_boards(player, die, boards, bar=False):
		# boards is a list containing starting boards
		# loop over the boards in boards list
		for i, board in enumerate(boards):
			new_boards = []
			#print i, repr(board)
			# check if bar move must be made
			if bar == True:
				try:
					# make a bar move, and return the resulting board
					destination = Board.get_home(Board.get_opponent(player)) + die * Board.get_direction(player)
					#print "bar dest: ", destination + 1
					bar_move = BarMove(player, die, board, destination)
					tmp_board = bar_move.make_move()
					print "BarMove"
				except IllegalMoveException:
					tmp_board = None
				# make sure tmp_board is not empty (will return None)
				# if not empty add to new_boards
				if tmp_board is not None:
					new_boards.append(tmp_board)
			# try normal or bear-off moves:
			else:	
				# loop over whole board
				for pos in range(Board.NUM_POINTS):
					# pos occupied by player
					if board.get_checkers(pos, player) > 0:
						try:
							# try to bear off checkers and return resulting board
							bear_off_move = BearOffMove(player, die, board, pos)
							tmp_board = bear_off_move.make_move()
							print "BearOffMove"
						except IllegalMoveException, e:
							try:
								# if bear off not possible:
								# try to make a normal move and return resulting board
								destination = pos + (die * Board.get_direction(player))
								normal_move = NormalMove(player, die, board, pos, destination)
								tmp_board = normal_move.make_move()
								print "NormalMove"
							except IllegalMoveException, e:
								tmp_board = None
						
						# make sure tmp_board is not empty (will return None)
						# if not empty add to new_boards
						#print tmp_board
						if tmp_board is not None:
							new_boards.append(tmp_board)
					
			# check if new boards were created
			# and if yes, replace each starting board in boards with
			# a list of possible boards originating from each starting board
			if len(new_boards) > 0:
				boards[i] = new_boards

		# flattens boards, takes sublist elements and puts them a new list
		# and returns a list containing all possible boards
		#print [item for sublist in boards for item in sublist]
		#print boards
		try:
			return [item for sublist in boards for item in sublist]
		except TypeError:
			print "boards:", boards
			return boards
		

	

# b = Board()
# d = Dice()
# d.roll()

# BoardFactory.generate_all_boards(0, d, b)

# # a handmade for loop in C-Style:
# # used to make for loops combined with more sophisticated testing conditions
# # usage: for i in cfor(0, lambda i: test function, lambda i: update function)
# # lambda x: x + 1 basically is syntactic sugar for def function(x): x + 1
# def cfor(first, test, update):
# 	while test(first):
# 		yield first
#		first = update(first)
# @classmethod
	# def generateMoves(cls, base):
	# 	""" Returns a set of all possible moves given the board situation
	# 		and using the given dice roll. """
	# 	# construction of moves and their objects:
	# 	# a move consists of 2 or 4 movements, contained in movements list
	# 	# equality is tested
	# 	result = set()
		
	# 	# if no more movements can be added, or no more moves are possible,
	# 	# return just this move
	# 	# here is why it only gives you one move, because when move is full,
	# 	# result is returned and function is exited
	# 	if base.isFull() or (not base.movePossible()):
	# 		result.add(base)
	# 		return result

	# 	# get current Board
	# 	board = base.getCurrentBoard()
	# 	player = base.player

	# 	# try to add any off-bar movements to base_move
	# 	if board.getBar(player) > 0:
	# 		# loop thru used dice
	# 		for i in range(len(base.used)):
	# 			# take the roll, which wasnt used yet
	# 			if base.used[i] != Move.USED:
	# 				try:
	# 					# create a new bar move by cloning from base_move
	# 					bar = Move(base)
	# 					# destination is position 1...6 in opponents homeboard
	# 					destination = (Board.getHome(Board.getOtherPlayer(player))
	# 									+ bar.used[i] * Board.getDirection(player))
	# 					# add the movement to the move
	# 					# updates intermediate board and adds movement to movements
	# 					# calls canUse() and apply()
	# 					bar_movement = BarMovement(player, destination)
	# 					bar.addMovement(bar_movement)
	# 					result.update(cls.generateMoves(bar))
	# 				# exceptions in the try block must be handled with the corresponding
	# 				# exception type in the except block, otherwise script ends
	# 				except IllegalMoveException, e:
	# 					#print type(e).__name__, "-", e.msg
	# 					break
	# 	# when no bar moves are possible,
	# 	# try normal moves
	# 	else:
	# 		# loop over whole board from start to end
	# 		for i in cfor(Board.getHome(Board.getOtherPlayer(player)) + Board.getDirection(player), lambda i: Board.onBoard(i), lambda i: i + Board.getDirection(player)):
	# 			# find players checkers
	# 			if board.getCheckers(i, player) > 0:
	# 				# when two different numbers were rolled
	# 				if len(base.used) == 2:
	# 					# loop over dice
	# 					for j in range(len(base.used)):
	# 						# check if die is unused
	# 						if base.used[j] != Move.USED:
	# 							try:
	# 								normal = Move(base)
	# 								destination = i + base.used[j] * Board.getDirection(player)
	# 								normal_movement = NormalMovement(player, i, destination)
	# 								normal.addMovement(normal_movement)
	# 								result.update(cls.generateMoves(normal))
	# 							except IllegalMoveException, e:
	# 								#print type(e).__name__, "-", e.msg
	# 								break
	# 				# when a double was rolled
	# 				elif len(base.used) == 4:
	# 					try:
	# 						normal = Move(base)
	# 						destination = i + base.dice.getDie1() * Board.getDirection(player)
	# 						normal_movement = NormalMovement(player, i, destination)
	# 						normal.addMovement(normal_movement)
	# 						result.update(cls.generateMoves(normal))
	# 					except IllegalMoveException, e:
	# 						#print type(e).__name__, "-", e.msg
	# 						break

	# 		# lastly try any bear-off moves
	# 		# loop over own homeboard
	# 		for i in cfor(Board.getHome(player) - Board.getDirection(player), lambda i: Board.inHomeBoard(player, i), lambda i: i - Board.getDirection(player)):
	# 			#print i
	# 			if board.getCheckers(i, player) > 0:
	# 				try:
	# 					bearoff = Move(base)
	# 					bearoff_movement = BearOffMovement(player, i)
	# 					bearoff.addMovement(bearoff_movement)
	# 					result.update(cls.generateMoves(bearoff))
	# 				except IllegalMoveException, e:
	# 					#print type(e).__name__, "-", e.msg
	# 					break

	# 	return result








