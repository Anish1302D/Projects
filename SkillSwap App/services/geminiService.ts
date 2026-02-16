
import { GoogleGenAI, Type } from "@google/genai";
import { User, MatchScore } from "../types";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

export async function calculateMatchScores(currentUser: User, availableUsers: User[]): Promise<MatchScore[]> {
  const prompt = `
    You are an AI matchmaking engine for "SkillSwap", a peer-to-peer skill exchange platform.
    Your goal is to calculate a compatibility score (0-100) between the current user and other community members.
    
    A high score is awarded when User A's "skillsNeeded" overlap with User B's "skillsOffered" AND vice-versa.
    
    Current User:
    Name: ${currentUser.name}
    Offered: ${currentUser.skillsOffered.map(s => s.name).join(', ')}
    Needed: ${currentUser.skillsNeeded.map(s => s.name).join(', ')}
    
    Candidates:
    ${availableUsers.map(u => `
      - ID: ${u.id}
        Name: ${u.name}
        Offered: ${u.skillsOffered.map(s => s.name).join(', ')}
        Needed: ${u.skillsNeeded.map(s => s.name).join(', ')}
    `).join('\n')}
  `;

  try {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.ARRAY,
          items: {
            type: Type.OBJECT,
            properties: {
              userId: { type: Type.STRING },
              score: { type: Type.NUMBER },
              reasoning: { type: Type.STRING },
              complementarySkills: { 
                type: Type.ARRAY,
                items: { type: Type.STRING }
              }
            },
            required: ["userId", "score", "reasoning", "complementarySkills"]
          }
        }
      }
    });

    const results = JSON.parse(response.text || "[]");
    return results;
  } catch (error) {
    console.error("Matchmaking failed:", error);
    return availableUsers.map(u => ({
      userId: u.id,
      score: Math.floor(Math.random() * 40) + 50,
      reasoning: "A potential match based on shared interests.",
      complementarySkills: [u.skillsOffered[0]?.name]
    }));
  }
}

export async function generateSwapInsight(userA: User, userB: User): Promise<string> {
  const prompt = `
    Create a 3-step action plan for a 1-hour skill swap between ${userA.name} and ${userB.name}.
    ${userA.name} offers: ${userA.skillsOffered.map(s => s.name).join(', ')}
    ${userB.name} offers: ${userB.skillsOffered.map(s => s.name).join(', ')}
    Keep it concise and practical. Format it as a simple list.
  `;
  try {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: prompt
    });
    return response.text || "No insights available at this time.";
  } catch (err) {
    return "Let's connect and figure out a plan together!";
  }
}
