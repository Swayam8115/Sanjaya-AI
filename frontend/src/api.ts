
export const sendMessage = async (message: string) => {
    const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: message }),
    });

    if (!response.ok) {
        throw new Error("Failed to send message");
    }

    return response.json();
};
