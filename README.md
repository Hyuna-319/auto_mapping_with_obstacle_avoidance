 🤖 로봇 청소기 기능 구현 & 객체 추적 알고리즘 학습
=============
로봇 주행 환경 장애물 회피 모델 개발 및 객체 추적 알고리즘 학습  



[프로젝트 기록](https://velog.io/@cherry0319/%EC%82%AC%EB%82%B4-%EC%B9%B4%ED%8E%98-%EC%84%9C%EB%B9%99-%EB%A1%9C%EB%B4%87-%EC%8B%9C%EB%AE%AC%EB%A0%88%EC%9D%B4%EC%85%98) 

<br>


인원 및 기간
-------------
* 3명: [김현아](https://github.com/Hyuna-319), [장석환](https://github.com/JSH0101), [홍유진](https://github.com/dbwls99706)
* 2024.11.26 ~ 2024.12.02 (7일)
  
<br> 

사용 기술
-------------
* Language : Python3
* OS : Linux Ubuntu 22.04 jammy
* Hardware : Turtlebot4
* Skills : ROS2 Humble Rviz2, Nav2, SLAM, Turtlebo4 Packages, OpenCV

  
<br>

특징
-------------

* Auto Mapping
  - `/map`의 OccupancyGrid 데이터를 활용하여 미탐사 영역(-1), 탐사된 자유 공간(0), 벽(100)을 구분하고 미탐사 영역을 탐지 및 검색
  - 탐색 완료 후 자동으로 다음 미탐사 영역을 목표 위치로 설정, 모든 영역 탐사 및 map 완성 자동화
  - nav2.yaml과 slam.yaml의 파라미터를 조정하여 Navigation2와 SLAM 성능 최적화

 
<br>

* Wall Follow
  - map 완성 후 `/exploration_done` 토픽에서 True를 수신하여 벽 따라가기 시작
  - 10초마다 방향을 전환하며 벽을 따라 이동하여 청소 범위를 확장


    
<br>

* Object Tracking
  - ORB (Oriented FAST and Rotated BRIEF) 알고리즘을 사용해 객체를 실시간으로 추적
  - 해밍 거리를 기준으로 특징점을 오름차순 정렬하여 가장 신뢰도 높은 매칭을 우선 처리
  - 정렬된 특징점의 좌표를 계산하고 매칭 결과를 시각적으로 표시하여 객체 추적 정확도 향상

<br>



보완 사항
-------------
* Auto Mapping 완료 후 Wall Follow가 자동으로 실행되도록 수정 필요



<br>
<br>


프로젝트 결과
-------------

<br>

**결과 이미지**

![결과 이미지](https://github.com/user-attachments/assets/29fc33bb-bf6a-49a9-b203-8069a74010d1)




<br>

**결과 동영상**

* Auto Mapping
  
[![Auto Mapping](https://github.com/user-attachments/assets/1470c2d8-6ba7-41c6-ac40-e5215a44fb3e)](https://youtu.be/tXpjtyQcmNI)


<br>

* Wall Follow


<br>
* Object Tracking



![결과 이미지](https://github.com/user-attachments/assets/3694009b-0584-4130-ba0b-cbf7c4c88f7b)
