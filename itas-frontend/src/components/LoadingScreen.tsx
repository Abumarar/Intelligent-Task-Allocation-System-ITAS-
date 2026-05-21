import { useEffect, useState } from "react";

export default function LoadingScreen({ onComplete }: { onComplete: () => void }) {
    const [isFading, setIsFading] = useState(false);

    useEffect(() => {
        // Play for 2.5 seconds, then start fade out
        const timer = setTimeout(() => {
            setIsFading(true);
            // Wait for fade animation to finish (e.g., 500ms) before unmounting
            setTimeout(onComplete, 500);
        }, 2500);

        return () => clearTimeout(timer);
    }, [onComplete]);

    return (
        <div
            className={`fixed inset-0 z-[9999] flex items-center justify-center bg-black transition-opacity duration-500 ${isFading ? "opacity-0" : "opacity-100"
                }`}
        >
            <video
                autoPlay
                loop
                muted
                playsInline
                className="h-full w-full object-cover"
            >
                <source src="/loading.mp4" type="video/mp4" />
                Your browser does not support the video tag.
            </video>
        </div>
    );
}
