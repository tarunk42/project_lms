#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${RED}Stopping AI-Powered LMS Platform${NC}"
echo -e "${BLUE}=========================================${NC}"

# Check if the process IDs file exists
if [ -f logs/process_ids.txt ]; then
    # Read PIDs from file
    read API_PID NGROK_PID WEB_PID < logs/process_ids.txt
    
    # Stop API server
    if ps -p $API_PID > /dev/null; then
        echo -e "${GREEN}Stopping API server (PID: $API_PID)...${NC}"
        kill -9 $API_PID 2>/dev/null || echo "Process already terminated."
    else
        echo -e "${RED}API server process not found.${NC}"
    fi
    
    # Stop ngrok
    if ps -p $NGROK_PID > /dev/null; then
        echo -e "${GREEN}Stopping ngrok tunnel (PID: $NGROK_PID)...${NC}"
        kill -9 $NGROK_PID 2>/dev/null || echo "Process already terminated."
    else
        echo -e "${RED}ngrok process not found.${NC}"
    fi
    
    # Stop web server
    if ps -p $WEB_PID > /dev/null; then
        echo -e "${GREEN}Stopping web server (PID: $WEB_PID)...${NC}"
        kill -9 $WEB_PID 2>/dev/null || echo "Process already terminated."
    else
        echo -e "${RED}Web server process not found.${NC}"
    fi
    
    # Remove the file
    rm logs/process_ids.txt
else
    # Try to find and kill processes by port
    echo -e "${RED}Process IDs file not found. Trying to stop by port numbers...${NC}"
    
    # Kill process on port 8000 (API server)
    if lsof -ti:8000 > /dev/null; then
        echo -e "${GREEN}Stopping process on port 8000...${NC}"
        lsof -ti:8000 | xargs kill -9
    else
        echo -e "${RED}No process found on port 8000.${NC}"
    fi
    
    # Kill process on port 5500 (Web server)
    if lsof -ti:5500 > /dev/null; then
        echo -e "${GREEN}Stopping process on port 5500...${NC}"
        lsof -ti:5500 | xargs kill -9
    else
        echo -e "${RED}No process found on port 5500.${NC}"
    fi
    
    # Find and kill ngrok processes
    if pgrep -f ngrok > /dev/null; then
        echo -e "${GREEN}Stopping ngrok processes...${NC}"
        pkill -f ngrok
    else
        echo -e "${RED}No ngrok processes found.${NC}"
    fi
fi

echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}All LMS services stopped successfully!${NC}"
echo -e "${BLUE}=========================================${NC}"
