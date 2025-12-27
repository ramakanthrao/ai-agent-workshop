import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import OpenAI from "openai";
import readline from "node:readline/promises";
import fs from "node:fs/promises";
import { stdin as input, stdout as output } from "node:process";

// 1. Setup Local LLM (LM Studio)
const openai = new OpenAI({ 
  baseURL: "http://localhost:1234/v1", 
  apiKey: "lm-studio" 
});

// 2. Setup MCP Client
const transport = new StdioClientTransport({
  command: "node",
  args: ["server.mjs"] // Ensure your FastMCP server file is named server.mjs
});

const client = new Client(
  { name: "CLI-Agent-Manager", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

const rl = readline.createInterface({ input, output });

async function getValidFilePath() {
  while (true) {
    const filePath = await rl.question("\nHello user, please enter your file path: ");
    
    try {
      await fs.access(filePath);
      return filePath;
    } catch {
      console.log("The file path is incorrect or inaccessible. Please re-enter.");
    }
  }
}

async function runAgent() {
  try {
    // Start by getting a valid path from the user
    const targetFile = await getValidFilePath();

    console.log("\n--- Connecting to MCP Server ---");
    await client.connect(transport);
    
    console.log(`Step 1: Extracting 'multiply' function from: ${targetFile}`);
    
    const sourceResult = await client.callTool({
      name: "get_function_source",
      arguments: { filePath: targetFile, functionName: "multiply" }
    });

    const rawCode = sourceResult.content[0].text;

    if (rawCode.includes("Function not found")) {
      console.log("Error: Could not find a 'multiply' function in that file.");
      return;
    }

    // Step 2: AI Logic
    console.log("Step 2: Sending code to LM Studio for analysis...");
    const completion = await openai.chat.completions.create({
      model: "any-model",
      messages: [
        { 
          role: "system", 
          content: "You are a code refactoring agent. Summarize the function provided and then fix it. Return the full code block only." 
        },
        { role: "user", content: `Code to fix:\n\n${rawCode}` }
      ]
    });

    const fixedCode = completion.choices[0].message.content;
    console.log("\n--- AI Summary & Suggestion ---");
    console.log(fixedCode);

    // Step 3: Confirmation before writing
    const confirm = await rl.question("\nWould you like to write these changes to the file? (yes/no): ");
    
    if (confirm.toLowerCase() === 'yes' || confirm.toLowerCase() === 'y') {
      console.log("Step 3: Writing changes to disk...");
      await client.callTool({
        name: "write_back_to_file",
        arguments: { filePath: targetFile, content: fixedCode }
      });
      console.log("Success! File updated.");
    } else {
      console.log("Write cancelled by user.");
    }

  } catch (error) {
    console.error("Agent Error:", error.message);
  } finally {
    rl.close();
    process.exit(0);
  }
}

runAgent();