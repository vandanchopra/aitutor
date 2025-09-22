import * as React from "react";
import { registerAllWidgetsForTesting, Dependencies } from "@khanacademy/perseus";
import { PerseusDependencies, PerseusDependenciesV2 } from "@khanacademy/perseus";
import {TestMathjax} from "./test-mathjax";

// We do nothing in this implementation, but it is easy to spy on the .Log of
// the PerseusDependencies in tests and then assert on the calls.
const LogForTesting = {
    log: () => {},
    error: () => {},
};

const testDependencies: PerseusDependencies = {
    // JIPT
    JIPT: {
        useJIPT: false,
    },
    graphieMovablesJiptLabels: {
        addLabel: (label, useMath) => {},
    },
    svgImageJiptLabels: {
        addLabel: (label, useMath) => {},
    },
    rendererTranslationComponents: {
        addComponent: (renderer) => -1,
        removeComponentAtIndex: (index) => {},
    },

    TeX: ({children}: {children: React.ReactNode}) => {
        return <span className="mock-TeX">{children}</span>;
    },

    // @ts-expect-error - TS2322 - Type '(str?: string | null | undefined) => string' is not assignable to type 'StaticUrlFn'.
    staticUrl: (str?: string | null) => {
        // We define the interface such that TypeScript can infer calls properly.
        // However, it means that return types are hard to match here in
        // the implementation.
        return `mockStaticUrl(${str})`;
    },

    // video widget
    useVideo: (id, kind) => {
        // Used by video-transcript-link.jsx.fixture.js
        if (id === "YoutubeId" && kind === "YOUTUBE_ID") {
            return {
                status: "success",
                data: {
                    video: {
                        id: "YoutubeVideo",
                        contentId: "contentId",
                        youtubeId: "YoutubeId",
                        title: "Youtube Video Title",
                        __typename: "Video",
                    },
                },
            };
        }
        if (id === "slug-video-id" && kind === "READABLE_ID") {
            return {
                status: "success",
                data: {
                    video: {
                        title: "Slug Video Title",
                        id: "VideoId",
                        youtubeId: "YoutubeId",
                        contentId: "contentId",
                        __typename: "Video",
                    },
                },
            };
        }

        return {
            status: "loading",
        };
    },

    InitialRequestUrl: {
        origin: "origin-test-interface",
        host: "host-test-interface",
        protocol: "protocol-test-interface",
    },

    isDevServer: false,
    kaLocale: "en",

    Log: LogForTesting,
};

const testDependenciesV2: PerseusDependenciesV2 = {
    analytics: {
        onAnalyticsEvent: async () => {},
    },
    useVideo: () => {
        return {
            status: "success",
            data: {
                video: null,
            },
        };
    },
};


export const TestDependencies: PerseusDependencies = {
    ...testDependencies,
    TeX: TestMathjax,
    staticUrl: (str) => str,
};


export const DependenciesV2: PerseusDependenciesV2 = {
    ...testDependenciesV2,
    // Override if necessary
};

// Initialize Perseus
registerAllWidgetsForTesting();
Dependencies.setDependencies(TestDependencies);