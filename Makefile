RM			= \rm -f

ECHO			= /bin/echo -e

CC			= gcc

BIN_DIR			= ./opti_module/bin

NAME			= $(BIN_DIR)/libmotion_detector_optimization.so

SRC_DIR			= src

SRCS			= $(SRC_DIR)/scanner_opti.c

OBJS			= $(SRCS:.c=.o)

CFLAGS			= -W -Wall -Werror -Wextra -fPIC

all:            	$(NAME)

$(NAME):		$(OBJS)
			@$(ECHO) "\e[0m"
			@mkdir -p $(BIN_DIR)
			@$(CC) $(OBJS) -o $(NAME) -shared $(LIBS) 2> /dev/null && \
			$(ECHO) "\e[32mAll done ! ==>\e[33m" $(NAME) "\e[32mcreated !\e[0m" || \
			$(ECHO) "\e[91;5m[ERROR]\e[25m Can't compile\e[33m" $(NAME) "\e[0m"

clean:
			@$(ECHO)n "\e[0mCleaning .o files..."
			@$(RM) $(OBJS)
			@$(ECHO) "	[\e[32mOk !\e[0m]"

fclean:         	clean
			@$(ECHO)n "\e[39mCleaning executable..."
			@$(RM) -r $(BIN_DIR)
			@$(ECHO) "	[\e[32mOk !\e[0m]"

re:             	fclean all

.c.o:			%.c
			@$(CC) -c $< -o $@ $(CFLAGS) && \
			$(ECHO) "\e[32m[OK]" $< "\e[93m"|| \
			$(ECHO) "\e[91;5m[ERR]\e[25m" $< "\e[93m"

.PHONY:         	all clean fclean re
