RM			= \rm -f

ECHO			= /bin/echo -e

CC			= gcc

BIN_DIR			= ./motion_detector/bin

NAME			= $(BIN_DIR)/libmotion_detector_optimization.so

SRC_DIR			= ./motion_detector/src

SRCS			= $(SRC_DIR)/scanner.c \
			$(SRC_DIR)/coord_list.c \
			$(SRC_DIR)/find_bounding_boxes.c \
			$(SRC_DIR)/bounding_box_data_struct.c \
			$(SRC_DIR)/packer.c \
			$(SRC_DIR)/packer_data_structs.c

OBJS			= $(SRCS:.c=.o)

CFLAGS			= -W -Wall -Werror -Wextra -fPIC -O3 \
			`pkg-config --cflags python3` \
			-I$(SRC_DIR) \
			-I`python3 -m site --user-site`/numpy/core/include

LIBS			= `pkg-config --libs python3`

all:            	$(NAME)

$(NAME):		$(OBJS)
			@mkdir -p $(BIN_DIR)
			$(CC) $(OBJS) -o $(NAME) -shared $(LIBS)

clean:
			$(RM) $(OBJS)

fclean:         	clean
			$(RM) -r $(BIN_DIR)

re:             	fclean all

.c.o:			%.c
			$(CC) -c $< -o $@ $(CFLAGS)

.PHONY:         	all clean fclean re
