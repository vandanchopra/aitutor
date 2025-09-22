import React, { useEffect, useState, useRef } from "react";
import { ServerItemRenderer } from "@khanacademy/perseus";
import type { PerseusItem } from "@khanacademy/perseus-core";
import { PerseusI18nProvider } from "../contexts/perseusI18nContext";
import { ExamContext } from "../contexts/ExamContext";
// import { scorePerseusItem, keScoreFromPerseusScore, } from "@khanacademy/perseus-score";
// import { testDependenciesV2 } from "../perseus-init";
import { storybookDependenciesV2 } from "../package/perseus/testing/test-dependencies";

const RendererComponent = () => {
    const [perseusItems, setPerseusItems] = useState<PerseusItem[]>([]);
    const [item, setItem] = useState(0);
    const [loading, setLoading] = useState(true);
    const { dispatch } = React.useContext(ExamContext);
    // const rendererRef = useRef<ServerItemRenderer>(null);

    useEffect(() => {
        fetch("http://localhost:8001/api/questions")
            .then((response) => response.json())
            .then((data) => {
                console.log("API response:", data);
                setPerseusItems(data);
                setLoading(false);
            })
            .catch((err) => {
                console.error("Failed to fetch questions:", err);
                setLoading(false);
            });
    }, []);

    const perseusItem = perseusItems[item] || {};

    return (
        <PerseusI18nProvider
            strings={{
                chooseNumAnswers: ({ numCorrect }: { numCorrect: string }) => 
                    `Select ${numCorrect} correct answer${numCorrect !== "1" ? "s" : ""}`,
                chooseAllAnswers: "Select all correct answers",
                chooseOneAnswer: "Select one answer",
            }}
        >
            <div style={{ padding: "20px" }}>
                {loading && <p>Loading questions...</p>}
                <button
                    onClick={() => {
                        const index = (item === perseusItems.length - 1) ? 0 : (item + 1);
                        console.log(`Item: ${index}`)
                        setItem(index)}
                    }
                    className="absolute bg-black rounded text-white p-2 right-8">
                        Next
                </button>
                {!loading && perseusItems.length >= 1 &&
                    <ServerItemRenderer
                        // ref={rendererRef}
                        problemNum={0}
                        item={perseusItem}
                        dependencies={storybookDependenciesV2}
                        apiOptions={(() => {
                            const options = {};
                            console.log("[DEBUG] RendererComponent apiOptions:", options);
                            return options;
                        })()}
                        linterContext={{
                            contentType: "",
                            highlightLint: true,
                            paths: [],
                            stack: [],
                        }}
                        showSolutions="none"
                        hintsVisible={0}
                        reviewMode={false}
                    />}
            </div>
        </PerseusI18nProvider>
    );
};

export default RendererComponent;
