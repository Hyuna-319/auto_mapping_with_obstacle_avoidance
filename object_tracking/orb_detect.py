import time
import cv2
import numpy as np

class VideoFrameSimulator:
    def __init__(self, video_file, max_fps=15):  # max_fps를 매개변수로 전달받음
        self.cap = cv2.VideoCapture(video_file)  # 비디오 파일 연결
        self.max_fps = max_fps

        # 비디오 FPS 가져오기
        video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        if video_fps <= 0:  # FPS를 가져오지 못한 경우 기본값 설정
            video_fps = 30  # 30 프레임으로 가정, 사용 비디오는 24.315 fps

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))  # 총 프레임 수, 시간*프레임수
        self.frame_interval_sec = 1 / max_fps  # 프레임 간 시간 간격 , 0.67ms
        self.frame_interval_n = int(video_fps // max_fps) if max_fps <= video_fps else 1  # 샘플링 간격 계산

    def iterate_frame(self):  # 프레임 하나씩 생성, 샘플링 간격에 따라 특정 프레임 반환
        if not self.cap.isOpened():
            print("Error: Unable to open video file")
            return

        frame_id = 0  # 프레임 id 추적, 첫 번째 프레임부터 시작 
        while True:
            ret, frame = self.cap.read()  # 다음 프레임 읽기
            if not ret:
                break

            # 샘플링 간격에 따라 프레임 반환
            if frame_id % self.frame_interval_n == 0:
                yield frame
                time.sleep(self.frame_interval_sec)  # 프레임 간 시간 간격 유지
            frame_id += 1

        self.cap.release()


def orb_tracking(video_file):
    # ORB 객체 생성: 최대 특징점 수와 매개변수 조정
    orb = cv2.ORB_create(nfeatures=2000, scaleFactor=1.1, nlevels=12)

    # 최대 특징점 개수(nfeatures): 탐지할 최대 특징점 개수 설정
    # 척도 피라미드 레벨(nlevels): 다중 해상도에서 특징점을 탐지하기 위한 레벨 수
    # 특징점 품질 임계값(scaleFactor): 이미지 피라미드 축소 비율, 낮을수록 더 많은 특징점을 탐지

    vid = VideoFrameSimulator(video_file)

    # 추적을 위한 변수 초기화
    prev_keypoints = None
    prev_descriptors = None
    prev_points = None

    # 특징 매칭을 위한 BFMatcher 객체 생성
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    for frame in vid.iterate_frame():
        # ORB를 사용하기 위해 프레임을 그레이스케일로 변환
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # ORB 특징점 탐지 및 계산
        keypoints, descriptors = orb.detectAndCompute(gray, None)

        # 현재 프레임의 복사본 생성 (추적 결과 표시용)
        tracked_frame = frame.copy()

        # 특징점을 추적하여 초록색 점으로 표시
        if prev_keypoints is not None and prev_descriptors is not None:
            # BFMatcher를 사용하여 특징 매칭 
            matches = bf.match(prev_descriptors, descriptors)  # 유사점 매칭 (해밍 거리)
            matches = sorted(matches, key=lambda x: x.distance)  # 가장 신뢰할 수 있는 매칭(해밍 거리가 낮은 )우선 처리

            # 매칭된 특징점의 좌표 계산
            matched_points = []
            for match in matches:
                pt = keypoints[match.trainIdx].pt
                matched_points.append(pt)
                cv2.circle(tracked_frame, (int(pt[0]), int(pt[1])), 3, (0, 255, 0), -1)  # 초록색 점

            prev_points = matched_points  # 매칭된 좌표 업데이트
        else:
            # 첫 번째 프레임에서는 탐지된 특징점 표시
            for kp in keypoints:
                pt = kp.pt
                cv2.circle(tracked_frame, (int(pt[0]), int(pt[1])), 3, (0, 255, 0), -1)  # 초록색 점

        # 현재 프레임 표시
        cv2.imshow("Object Tracking", tracked_frame)

        # 현재 데이터를 이전 데이터로 업데이트
        prev_keypoints = keypoints
        prev_descriptors = descriptors

        # 'q' 키를 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()


# 예제 실행
if __name__ == "__main__":
    video_file = "/home/hyuna/프로젝트3_tracking/test2.MOV"  # 비디오 파일 경로 입력
    orb_tracking(video_file) 
