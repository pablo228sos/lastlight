import { Composition } from "remotion";
import { LastlightFilm } from "./Film";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Lastlight62"
        component={LastlightFilm}
        durationInFrames={1860}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
